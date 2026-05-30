class UserProfile {
  const UserProfile({
    required this.id,
    required this.email,
    this.displayName,
    required this.isPremium,
    required this.isAdmin,
    required this.isVerified,
  });

  final String id;
  final String email;
  final String? displayName;
  final bool isPremium;
  final bool isAdmin;
  final bool isVerified;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: (json['id'] ?? '') as String,
      email: (json['email'] ?? '') as String,
      displayName: json['display_name'] as String?,
      isPremium: (json['is_premium'] ?? false) as bool,
      isAdmin: (json['is_admin'] ?? false) as bool,
      isVerified: (json['is_verified'] ?? false) as bool,
    );
  }
}
