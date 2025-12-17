#!/usr/bin/env python3
"""
Data Quality Validator for MRO Supply Scraper
Validates scraped product data and tracks quality metrics
"""

import re
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of product validation"""

    def __init__(self, is_valid: bool, score: float, issues: List[str] = None):
        """
        Initialize validation result

        Args:
            is_valid: Whether product passes validation
            score: Completeness score (0-100)
            issues: List of validation issues
        """
        self.is_valid = is_valid
        self.score = score
        self.issues = issues or []
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        status = "✓ Valid" if self.is_valid else "✗ Invalid"
        return f"{status} (score: {self.score:.1f}%) - {len(self.issues)} issues"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'score': self.score,
            'issues': self.issues,
            'timestamp': self.timestamp.isoformat()
        }


class DataValidator:
    """
    Product data quality validator

    Validation rules:
    - Required fields: url, title, sku
    - Optional fields: price, brand, category, images
    - Title length > 10 chars
    - Price contains digits
    - At least 1 image
    - Completeness score > 30%
    """

    # Field weights for completeness score
    FIELD_WEIGHTS = {
        'url': 15,
        'title': 15,
        'sku': 15,
        'price': 10,
        'description': 10,
        'brand': 8,
        'category': 8,
        'specifications': 7,
        'images': 7,
        'availability': 5
    }

    # Required fields
    REQUIRED_FIELDS = ['url', 'title', 'sku']

    # Minimum values
    MIN_TITLE_LENGTH = 10
    MIN_COMPLETENESS_SCORE = 30.0
    QUALITY_ALERT_THRESHOLD = 80.0  # Alert if quality drops below this

    def __init__(self, config=None, notifier=None):
        """
        Initialize validator

        Args:
            config: Configuration object
            notifier: Optional notifier for alerts
        """
        self.config = config
        self.notifier = notifier

        # Validation statistics
        self.total_validated = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.issue_counts = defaultdict(int)
        self.completeness_scores = []

        # Tracking
        self.last_quality_alert = 0

        logger.info("Data validator initialized")

    def validate_product(self, product: Dict) -> ValidationResult:
        """
        Validate a single product

        Args:
            product: Product dictionary to validate

        Returns:
            ValidationResult: Validation result
        """
        if not product:
            return ValidationResult(False, 0.0, ["Product is None or empty"])

        issues = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not product.get(field):
                issues.append(f"Missing required field: {field}")
                self.issue_counts[f"missing_{field}"] += 1

        # Validate URL
        url = product.get('url', '')
        if url and not self._is_valid_url(url):
            issues.append("Invalid URL format")
            self.issue_counts['invalid_url'] += 1

        # Validate title
        title = product.get('title', '')
        if title:
            if len(title) < self.MIN_TITLE_LENGTH:
                issues.append(f"Title too short (< {self.MIN_TITLE_LENGTH} chars)")
                self.issue_counts['title_too_short'] += 1
        else:
            issues.append("Missing title")
            self.issue_counts['missing_title'] += 1

        # Validate SKU
        sku = product.get('sku', '')
        if sku and not self._is_valid_sku(sku):
            issues.append("Invalid SKU format")
            self.issue_counts['invalid_sku'] += 1

        # Validate price (optional but should be valid if present)
        price = product.get('price')
        if price:
            if not self._is_valid_price(price):
                issues.append("Invalid price format")
                self.issue_counts['invalid_price'] += 1
        else:
            issues.append("Missing price")
            self.issue_counts['missing_price'] += 1

        # Validate images
        images = product.get('images', [])
        if not images or len(images) == 0:
            issues.append("No product images")
            self.issue_counts['no_images'] += 1
        else:
            # Check image URLs
            invalid_images = [img for img in images if not self._is_valid_url(img)]
            if invalid_images:
                issues.append(f"{len(invalid_images)} invalid image URLs")
                self.issue_counts['invalid_image_urls'] += 1

        # Calculate completeness score
        score = self._calculate_completeness(product)
        self.completeness_scores.append(score)

        # Determine if valid
        is_valid = (
            len([i for i in issues if 'Missing required field' in i]) == 0 and
            score >= self.MIN_COMPLETENESS_SCORE
        )

        # Update statistics
        self.total_validated += 1
        if is_valid:
            self.valid_count += 1
        else:
            self.invalid_count += 1

        # Check if should alert
        self._check_quality_threshold()

        # Create result
        result = ValidationResult(is_valid, score, issues)

        if not is_valid:
            logger.warning(f"Validation failed for {url}: {result}")

        return result

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        if not url:
            return False

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))

    def _is_valid_sku(self, sku: str) -> bool:
        """Check if SKU is valid"""
        if not sku:
            return False

        # SKU should be alphanumeric with possible hyphens/underscores
        # and have reasonable length
        if len(sku) < 3 or len(sku) > 50:
            return False

        # Check format
        return bool(re.match(r'^[A-Z0-9\-_]+$', sku, re.IGNORECASE))

    def _is_valid_price(self, price) -> bool:
        """Check if price is valid"""
        if price is None:
            return False

        # Convert to string for checking
        price_str = str(price)

        # Should contain digits
        if not re.search(r'\d', price_str):
            return False

        # Try to extract numeric value
        try:
            # Remove currency symbols and commas
            numeric_str = re.sub(r'[^\d.]', '', price_str)
            if numeric_str:
                value = float(numeric_str)
                # Price should be positive and reasonable
                return 0 < value < 1000000
        except ValueError:
            pass

        return False

    def _calculate_completeness(self, product: Dict) -> float:
        """
        Calculate product data completeness score

        Returns:
            float: Score from 0-100
        """
        total_weight = sum(self.FIELD_WEIGHTS.values())
        earned_weight = 0

        for field, weight in self.FIELD_WEIGHTS.items():
            value = product.get(field)

            if value:
                # Field is present
                if isinstance(value, str):
                    # String field - check if not empty
                    if value.strip():
                        earned_weight += weight
                elif isinstance(value, (list, dict)):
                    # Collection - check if not empty
                    if len(value) > 0:
                        earned_weight += weight
                else:
                    # Other types (numbers, booleans, etc.)
                    earned_weight += weight

        score = (earned_weight / total_weight) * 100
        return round(score, 2)

    def _check_quality_threshold(self):
        """Check if quality has dropped below threshold"""
        if self.total_validated < 100:
            # Need minimum sample size
            return

        # Calculate recent quality
        if self.total_validated % 50 == 0:  # Check every 50 products
            recent_quality = (self.valid_count / self.total_validated) * 100

            if recent_quality < self.QUALITY_ALERT_THRESHOLD:
                # Quality below threshold
                logger.warning(
                    f"Data quality below threshold: {recent_quality:.1f}% "
                    f"(threshold: {self.QUALITY_ALERT_THRESHOLD}%)"
                )

                # Send alert (rate limited to once per hour)
                import time
                if time.time() - self.last_quality_alert > 3600:
                    self._send_quality_alert(recent_quality)
                    self.last_quality_alert = time.time()

    def _send_quality_alert(self, quality: float):
        """Send quality alert"""
        if not self.notifier:
            return

        top_issues = self.get_top_issues(5)

        self.notifier.send_alert(
            f"Data quality dropped to {quality:.1f}%",
            {
                "quality_percent": quality,
                "threshold": self.QUALITY_ALERT_THRESHOLD,
                "total_validated": self.total_validated,
                "valid_count": self.valid_count,
                "invalid_count": self.invalid_count,
                "top_issues": top_issues
            }
        )

    def get_validation_stats(self) -> Dict:
        """
        Get validation statistics

        Returns:
            dict: Validation statistics
        """
        if self.total_validated == 0:
            return {
                'total_validated': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'quality_percent': 0,
                'avg_completeness': 0
            }

        quality = (self.valid_count / self.total_validated) * 100
        avg_completeness = (
            sum(self.completeness_scores) / len(self.completeness_scores)
            if self.completeness_scores else 0
        )

        return {
            'total_validated': self.total_validated,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'quality_percent': round(quality, 2),
            'avg_completeness': round(avg_completeness, 2),
            'top_issues': self.get_top_issues(10)
        }

    def get_top_issues(self, limit: int = 10) -> List[Dict]:
        """
        Get most common validation issues

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of issue dictionaries
        """
        # Sort issues by count
        sorted_issues = sorted(
            self.issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'issue': issue, 'count': count}
            for issue, count in sorted_issues[:limit]
        ]

    def reset_stats(self):
        """Reset validation statistics"""
        self.total_validated = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.issue_counts.clear()
        self.completeness_scores.clear()
        logger.info("Validation statistics reset")

    def is_quality_acceptable(self, min_quality: float = None) -> bool:
        """
        Check if current quality is acceptable

        Args:
            min_quality: Minimum acceptable quality (default: threshold)

        Returns:
            bool: True if quality is acceptable
        """
        if self.total_validated < 10:
            return True  # Not enough data

        threshold = min_quality or self.QUALITY_ALERT_THRESHOLD
        current_quality = (self.valid_count / self.total_validated) * 100

        return current_quality >= threshold


if __name__ == '__main__':
    # Test validator
    import sys
    sys.path.insert(0, '.')

    print("Data Validator Test")
    print("=" * 60)

    validator = DataValidator()

    # Test Case 1: Valid product
    print("\n1. Testing valid product...")
    valid_product = {
        'url': 'https://example.com/product/123',
        'title': 'High Quality Industrial Wrench Set',
        'sku': 'WRN-001',
        'price': '$49.99',
        'description': 'Professional grade wrench set',
        'brand': 'ToolMaster',
        'category': 'Hand Tools',
        'images': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg'],
        'availability': 'In Stock'
    }

    result = validator.validate_product(valid_product)
    print(f"   Result: {result}")
    print(f"   Score: {result.score}%")

    # Test Case 2: Invalid product (missing required fields)
    print("\n2. Testing invalid product (missing fields)...")
    invalid_product = {
        'url': 'https://example.com/product/456',
        'title': 'Short',  # Too short
        # Missing SKU
        'price': 'invalid',  # Invalid price
        # No images
    }

    result = validator.validate_product(invalid_product)
    print(f"   Result: {result}")
    print(f"   Score: {result.score}%")
    print(f"   Issues: {result.issues}")

    # Test Case 3: Partially complete product
    print("\n3. Testing partially complete product...")
    partial_product = {
        'url': 'https://example.com/product/789',
        'title': 'Basic Screwdriver',
        'sku': 'SCR-001',
        'price': '$9.99',
        # Missing optional fields
    }

    result = validator.validate_product(partial_product)
    print(f"   Result: {result}")
    print(f"   Score: {result.score}%")

    # Show statistics
    print("\n4. Validation Statistics:")
    stats = validator.get_validation_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Validator test completed")
