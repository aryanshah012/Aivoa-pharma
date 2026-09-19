# Security Policy

## Supported Version

The latest version on the `main` branch is the actively maintained version of AIVOA Pharma QMS.

## Reporting a Vulnerability

Please do **not** open a public issue for a security vulnerability.

Instead, contact the maintainer privately through the email listed on the GitHub profile and include:

- a clear description of the issue
- affected component or endpoint
- reproduction steps or proof of concept
- potential impact
- suggested mitigation, if known

Please avoid including real credentials, private customer data, payment information, or other sensitive data in reports.

## Security Principles

- Secrets and API keys must never be committed to the repository.
- Use the provided `.env.example` files for local configuration.
- Dependencies should be kept up to date.
- External inputs must be validated before they reach privileged actions.
- AI-generated outputs must not bypass deterministic safety checks or human-review requirements where those controls exist.

Security fixes should be tested before release and documented in the relevant changelog or release notes when appropriate.
