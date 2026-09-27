# Fixed Release Signing

Package name: `com.tianxian.stockinsight`

Expected release certificate SHA-256:

```text
5D:19:74:AB:CB:0D:B5:C8:D7:25:0C:02:39:71:37:FC:1A:35:4F:0C:9E:2C:3F:35:BD:79:6C:D9:66:C9:88:64
```

The release workflow fails if the APK certificate does not match this fingerprint.
The private JKS and GitHub Secret values are intentionally NOT stored in this repository.
Keep the separate signing backup offline and never commit it.
