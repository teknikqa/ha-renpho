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

The integration polls every 30 minutes (change it with the integration's
**Configure** button, from 5 minutes to 24 hours). It talks to
`cloud.renpho.com`, never to the scale, so a weigh-in appears only after the Renpho Health app has
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

## Troubleshooting

To see what the integration is doing, add this to `configuration.yaml` and
restart:

```yaml
logger:
  logs:
    custom_components.renpho_cloud: debug
```

- **"Renpho rejected that email and password".** Use the email and password of
  the Renpho Health app (blue icon), not the older Renpho app. Accounts that
  sign in with Google or Apple have no password and cannot log in here.
- **"The Renpho cloud refused the sign-in request".** The server answered but
  not with a bad-password code. The Home Assistant log has its code and
  message. Code `-114` ("Decryption failed") means the server could not read
  the request. It happens when the app version is missing or is 8.0.0 or
  later, so please open an issue with the log line.
- **"Could not reach the Renpho cloud".** Home Assistant could not connect to
  `cloud.renpho.com`. Check its internet access and DNS.
- **Sensors show an old weigh-in.** Update to v0.1.1 or later. Earlier
  versions read only the first 50 records, which are the oldest on some
  accounts.
- **The phone app logged you out.** Renpho allows one active session per
  account, so any login ends the other one. The integration keeps its session
  token and logs in again only when the token expires or you re-enter your
  password.
- **A weigh-in is missing.** The integration reads the cloud, not the scale.
  Open the Renpho Health app so it syncs, then wait for the next poll (30 minutes unless you changed it).

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
