class PurchaseVerification {
  const PurchaseVerification({
    required this.success,
    required this.isPremium,
    this.premiumExpiresAt,
    this.platform,
    this.productId,
    this.verification,
  });

  final bool success;
  final bool isPremium;
  final String? premiumExpiresAt;
  final String? platform;
  final String? productId;
  final String? verification;

  factory PurchaseVerification.fromJson(Map<String, dynamic> json) {
    return PurchaseVerification(
      success: (json['success'] ?? false) as bool,
      isPremium: (json['is_premium'] ?? false) as bool,
      premiumExpiresAt: json['premium_expires_at'] as String?,
      platform: json['platform'] as String?,
      productId: json['product_id'] as String?,
      verification: json['verification'] as String?,
    );
  }
}
