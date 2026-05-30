import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../l10n/app_localizations.dart';
import '../../data/oauth_gateway.dart';
import '../../domain/models/auth_tokens.dart';
import '../../domain/models/oauth_identity.dart';
import '../providers/auth_api_provider.dart';
import '../providers/auth_session_actions.dart';
import '../utils/auth_error_mapper.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _displayNameController = TextEditingController();

  bool _isRegister = false;
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _displayNameController.dispose();
    super.dispose();
  }

  Future<void> _completeAuth(AuthTokens tokens) async {
    await ref.read(authSessionActionsProvider).completeLogin(tokens);
    if (!mounted) {
      return;
    }
    context.go('/feed');
  }

  Future<void> _submit() async {
    if (_isSubmitting) {
      return;
    }

    setState(() {
      _errorMessage = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    final l10n = AppLocalizations.of(context)!;
    final api = ref.read(authApiServiceProvider);

    try {
      final tokens = _isRegister
          ? await api.register(
              email: _emailController.text,
              password: _passwordController.text,
              displayName: _displayNameController.text,
            )
          : await api.login(
              email: _emailController.text,
              password: _passwordController.text,
            );

      await _completeAuth(tokens);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = mapAuthError(error, l10n);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  Future<void> _oauthSignIn({
    required String provider,
    required Future<OAuthIdentity> Function() signIn,
  }) async {
    if (_isSubmitting) {
      return;
    }

    setState(() {
      _errorMessage = null;
      _isSubmitting = true;
    });

    final l10n = AppLocalizations.of(context)!;
    final api = ref.read(authApiServiceProvider);

    try {
      final identity = await signIn();
      final tokens = await api.oauthLogin(
        provider: provider,
        providerId: identity.providerId,
        email: identity.email,
        displayName: identity.displayName,
        avatarUrl: identity.avatarUrl,
      );
      await _completeAuth(tokens);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = mapAuthError(error, l10n);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final oauthGateway = ref.watch(oauthGatewayProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isRegister ? l10n.registerTitle : l10n.loginTitle),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              _isRegister ? l10n.registerDescription : l10n.loginDescription,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            if (oauthGateway.supportsGoogleSignIn || oauthGateway.supportsAppleSignIn) ...[
              if (oauthGateway.supportsGoogleSignIn)
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _isSubmitting
                        ? null
                        : () => _oauthSignIn(
                              provider: 'google',
                              signIn: oauthGateway.signInWithGoogle,
                            ),
                    icon: const Icon(Icons.g_mobiledata, size: 28),
                    label: Text(l10n.loginWithGoogleAction),
                  ),
                ),
              if (oauthGateway.supportsAppleSignIn) ...[
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _isSubmitting
                        ? null
                        : () => _oauthSignIn(
                              provider: 'apple',
                              signIn: oauthGateway.signInWithApple,
                            ),
                    icon: const Icon(Icons.apple),
                    label: Text(l10n.loginWithAppleAction),
                  ),
                ),
              ],
              const SizedBox(height: 24),
              Row(
                children: [
                  const Expanded(child: Divider()),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      l10n.loginOrDivider,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                  const Expanded(child: Divider()),
                ],
              ),
              const SizedBox(height: 24),
            ],
            Form(
              key: _formKey,
              child: Column(
                children: [
                  TextFormField(
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: InputDecoration(
                      labelText: l10n.loginEmailLabel,
                      border: const OutlineInputBorder(),
                    ),
                    validator: (value) {
                      final email = value?.trim() ?? '';
                      if (email.isEmpty || !email.contains('@')) {
                        return l10n.loginEmailValidation;
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  if (_isRegister) ...[
                    TextFormField(
                      controller: _displayNameController,
                      textCapitalization: TextCapitalization.words,
                      decoration: InputDecoration(
                        labelText: l10n.registerDisplayNameLabel,
                        border: const OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  TextFormField(
                    controller: _passwordController,
                    obscureText: true,
                    autofillHints: _isRegister
                        ? const [AutofillHints.newPassword]
                        : const [AutofillHints.password],
                    decoration: InputDecoration(
                      labelText: l10n.loginPasswordLabel,
                      border: const OutlineInputBorder(),
                    ),
                    validator: (value) {
                      final password = value ?? '';
                      if (password.length < 6) {
                        return l10n.loginPasswordValidation;
                      }
                      return null;
                    },
                  ),
                  if (_errorMessage != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      _errorMessage!,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.error,
                          ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _isSubmitting ? null : _submit,
                      child: _isSubmitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(
                              _isRegister
                                  ? l10n.registerSubmitAction
                                  : l10n.loginSubmitAction,
                            ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _isSubmitting
                  ? null
                  : () {
                      setState(() {
                        _isRegister = !_isRegister;
                        _errorMessage = null;
                      });
                    },
              child: Text(
                _isRegister ? l10n.loginSwitchAction : l10n.registerSwitchAction,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
