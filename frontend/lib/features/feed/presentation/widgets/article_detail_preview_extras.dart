import 'package:flutter/material.dart';

import '../../../../shared/widgets/skeleton_line.dart';

class ArticleDetailPreviewExtras extends StatelessWidget {
  const ArticleDetailPreviewExtras({super.key});

  @override
  Widget build(BuildContext context) {
    final contentWidth = MediaQuery.sizeOf(context).width - 32;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SkeletonLine(width: 140, height: 12),
        const SizedBox(height: 16),
        SkeletonLine(width: contentWidth, height: 14),
        const SizedBox(height: 8),
        SkeletonLine(width: contentWidth, height: 14),
        const SizedBox(height: 8),
        const SkeletonLine(width: 220, height: 14),
      ],
    );
  }
}
