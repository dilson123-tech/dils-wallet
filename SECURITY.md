# Security Policy

## Supported Versions

Aurea Gold is an active production-oriented fintech platform under continuous development.
Security fixes are prioritized for the current `main` branch and the latest production-aligned deployment.

| Version | Supported |
|---------|-----------|
| main    | ✅        |
| older branches / legacy snapshots | ❌ |

## Reporting a Vulnerability

If you believe you have found a security vulnerability in Aurea Gold, please report it privately and responsibly.

### Please include
- A clear description of the issue
- Steps to reproduce
- Impact assessment
- Affected area or component
- Any proof of concept, logs, or screenshots if relevant

## Responsible Disclosure

Please do **not** disclose vulnerabilities publicly before a fix has been evaluated and, when necessary, deployed.

We ask reporters to give reasonable time for investigation, mitigation, and validation before any public disclosure.

## Scope

This policy applies to the main security-sensitive areas of the project, including but not limited to:
- authentication and authorization
- PIX and payment-related flows
- admin and operational controls
- API endpoints and protected resources
- deployment and configuration issues
- secrets exposure
- tenant or account isolation issues

## Out of Scope

The following are generally out of scope unless they create real security impact:
- purely theoretical issues with no practical exploit path
- missing best-practice headers without exploitability
- low-risk informational findings with no security consequence
- issues in clearly marked legacy or experimental files not used in active flows

## Response Approach

Aurea Gold will make a best effort to:
1. acknowledge receipt of a valid report
2. assess severity and scope
3. prioritize remediation
4. validate the fix
5. communicate closure when appropriate

## Notes

Security is treated as a product priority because Aurea Gold is positioned as a real fintech platform, not a demo repository.
