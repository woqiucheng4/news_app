import 'package:flutter/material.dart';

import 'ticker_mode_animation.dart';

class RotatingIcon extends StatefulWidget {
  const RotatingIcon({
    super.key,
    required this.icon,
    this.size = 20,
  });

  final IconData icon;
  final double size;

  @override
  State<RotatingIcon> createState() => _RotatingIconState();
}

class _RotatingIconState extends State<RotatingIcon>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    syncAnimationWithTickerMode(context, _controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RotationTransition(
      turns: _controller,
      child: Icon(widget.icon, size: widget.size),
    );
  }
}
