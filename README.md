# Renpho Health for Home Assistant

Custom integration that reads your latest weigh-in from the Renpho Health
cloud and exposes it as Home Assistant sensors.

> **Unofficial.** Not affiliated with Renpho. It uses the same private API as
> the Renpho Health mobile app, which can change without notice.
>
> **Status: early.** Sign-in and reading measurements are confirmed against
> one live account and one scale. It has not yet run inside a real Home
> Assistant install.

## What you get

One device per Renpho account, with these sensors:

| Sensor | Unit |
| --- | --- |
| Weight, muscle mass, skeletal muscle mass, bone mass, fat-free weight | kg (change to lb or st per entity in the UI) |
| Body fat, body water, skeletal muscle, protein, subcutaneous fat | % |
| BMI, visceral fat, body score, waist-to-hip ratio | none |
| Fat mass and muscle mass for each arm, each leg and the trunk | kg; disabled by default; only scales with hand electrodes measure them |
| Basal metabolic rate | kcal/d |
| Body age | years |
| Last measurement | timestamp |
| Heart rate, cardiac index | disabled by default; only some scales measure them |

A sensor reads `unknown` when the scale did not measure that value.

The integration polls every 30 minutes. It talks to `cloud.renpho.com`, never
to the scale, so a weigh-in appears only after the Renpho Health app has
synced it.

## Install

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/teknikqa/ha-renpho` as an **Integration**.
2. Download **Renpho Health** and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Renpho Health**.
4. Sign in with your Renpho Health app email and password.

If your password changes, Home Assistant asks you to sign in again.

## Limits

- Only the account owner's measurements. Family members on the same account
  are not read yet.
- Email and password accounts only. Google and Apple sign-in are not supported.
- Requires Home Assistant 2025.11 or newer.

## Live check

Prints the newest raw record for your account, and the order the server
returns records in, without Home Assistant:

```sh
uv sync
RENPHO_EMAIL=you@example.com RENPHO_PASSWORD=... \
  uv run python custom_components/renpho_cloud/api.py
```

## Develop

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

### Release

HACS offers each GitHub release as an update.
[release-please](https://github.com/googleapis/release-please) cuts them:

1. Push [Conventional Commits](https://www.conventionalcommits.org/) to
   `main`. `fix:` and `feat:` commits are releasable; `docs:`, `test:` and
   `chore:` are not.
2. release-please opens or updates a release PR that bumps the version and
   writes `CHANGELOG.md`.
3. Merge that PR. release-please tags the commit and publishes the release.

## Credits

The wire protocol (endpoints, encryption) was documented by
[forkerer/RenphoGarminSync-CLI](https://github.com/forkerer/RenphoGarminSync-CLI)
and [danvaneijck/renpho-api](https://github.com/danvaneijck/renpho-api).
[DiscountDarcy/ha-renpho-health](https://github.com/DiscountDarcy/ha-renpho-health)
is an earlier Home Assistant integration for the same API. This project shares
no code with any of them.

## License

Apache-2.0. See [LICENSE](./LICENSE).
