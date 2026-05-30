import 'package:flutter/material.dart';

class SourceFavicon extends StatelessWidget {
  const SourceFavicon({
    super.key,
    required this.faviconUrl,
    this.size = 18,
  });

  final String? faviconUrl;
  final double size;

  @override
  Widget build(BuildContext context) {
    final fallback = Icon(
      Icons.public,
      size: size * 0.75,
      color: Theme.of(context).colorScheme.onSurfaceVariant,
    );

    if (faviconUrl == null || faviconUrl!.trim().isEmpty) {
      return SizedBox(width: size, height: size, child: fallback);
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(size / 4),
      child: Image.network(
        faviconUrl!,
        width: size,
        height: size,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) {
          return SizedBox(width: size, height: size, child: fallback);
        },
      ),
    );
  }
}
