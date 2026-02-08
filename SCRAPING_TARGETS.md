# スクレイピング設計ドキュメント

Instagram Scraping Systemの国別スクレイピングターゲット設定

---

## 概要

このシステムは、各国の日本人ワーホリ・留学生・駐在員向けに最適化されたInstagram情報を収集します。

### 処理フロー

```
1. Apifyでターゲットから投稿を取得
2. 日付フィルター（14日以内のみ）
3. 重複フィルター（DB既存をスキップ）
4. Gemini APIでカテゴリ分類
5. 優先順位でソート（Job > House > Event > Ignore）
6. Supabaseに保存
```

---

## 国別ターゲット設定

### 🇨🇦 Toronto (Canada)

| 種別 | ターゲット | 説明 |
|---|---|---|
| ハッシュタグ | `#torontojobs` | 求人情報 |
| ハッシュタグ | `#torontorentals` | 賃貸情報 |
| ハッシュタグ | `#トロント求人` | 日本語求人 |
| ハッシュタグ | `#torontoevents` | イベント情報 |
| アカウント | `@blogto` | トロントニュース・イベント |
| アカウント | `@torontolife` | ライフスタイル情報 |
| アカウント | `@sansoteiramen` | 日本食レストラン（求人あり） |
| アカウント | `@gyukaku` | 牛角（求人頻度高い） |
| アカウント | `@kibosushi_official` | KIBO寿司（寿司シェフ求人） |
| アカウント | `@hibachicanada` | Hibachi（複数ポジション求人） |

---

### 🇹🇭 Thailand

> ⚠️ タイにはワーホリ制度がないため、駐在員・現地採用向け情報が中心

| 種別 | ターゲット | 説明 |
|---|---|---|
| ハッシュタグ | `#bangkokjobs` | バンコク求人 |
| ハッシュタグ | `#bangkokrentals` | バンコク賃貸 |
| ハッシュタグ | `#タイ就職` | 日本語就職情報 |
| ハッシュタグ | `#バンコク駐在` | 駐在員向け |
| ハッシュタグ | `#バンコク生活` | 生活情報 |
| ハッシュタグ | `#thailandexpat` | 外国人向け全般 |
| アカウント | `@renosy_thailand` | 日系不動産（住居情報） |
| アカウント | `@bangkokfudosan` | バンコク不動産 |

---

### 🇵🇭 Philippines

> ℹ️ 語学留学生向け情報が中心

| 種別 | ターゲット | 説明 |
|---|---|---|
| ハッシュタグ | `#cebulife` | セブ島生活 |
| ハッシュタグ | `#manilalife` | マニラ生活 |
| ハッシュタグ | `#セブ島留学` | 留学生向け |
| ハッシュタグ | `#フィリピン求人` | 求人情報 |
| ハッシュタグ | `#cebuenglish` | 英語留学 |
| ハッシュタグ | `#philippinesexpat` | 外国人向け |
| アカウント | `@cebuenglish` | セブ英語留学情報 |

---

### 🇬🇧 UK (イギリス)

| 種別 | ターゲット | 説明 |
|---|---|---|
| ハッシュタグ | `#londonjobs` | ロンドン求人 |
| ハッシュタグ | `#londonrentals` | ロンドン賃貸 |
| ハッシュタグ | `#イギリスワーホリ` | ワーホリ向け |
| ハッシュタグ | `#ロンドン生活` | 生活情報 |
| ハッシュタグ | `#londonjapan` | 日本人コミュニティ |
| ハッシュタグ | `#ukworkingholiday` | ワーホリ全般 |
| アカウント | `@japanhouseld` | Japan House London（文化・イベント） |
| アカウント | `@mixb_london` | MixB（求人・住居掲示板） |

---

### 🇦🇺 Australia

| 種別 | ターゲット | 説明 |
|---|---|---|
| ハッシュタグ | `#sydneyjobs` | シドニー求人 |
| ハッシュタグ | `#melbournejobs` | メルボルン求人 |
| ハッシュタグ | `#オーストラリアワーホリ` | ワーホリ向け |
| ハッシュタグ | `#シドニー生活` | 生活情報 |
| ハッシュタグ | `#メルボルンカフェ` | カフェ求人（ワーホリ人気） |
| ハッシュタグ | `#australiaworkingholiday` | ワーホリ全般 |
| アカウント | `@nichigopress` | 日豪プレス（日本人コミュニティメディア） |
| アカウント | `@izakayadomo` | 居酒屋DOMO（メルボルン求人） |

---

## フィルター設定

| 項目 | 値 | 説明 |
|---|---|---|
| 日付フィルター | 14日 | 14日以上前の投稿はスキップ |
| 重複フィルター | ON | DB既存のshortcodeはスキップ |
| 取得上限 | 10件 | 1回の実行で最大10件処理 |

---

## カテゴリ優先順位

Gemini APIで分類後、以下の優先順位でソート・保存：

1. **Job** 💼 - 求人・採用情報
2. **House** 🏠 - 賃貸・ルームシェア情報
3. **Event** 🎉 - イベント・ミートアップ情報
4. **Ignore** 🚫 - その他・無関係

---

## メンテナンス

### ターゲット追加方法

`scraper.py` の `COUNTRY_TARGETS` を編集：

```python
"NewCountry": {
    "hashtags": ["hashtag1", "hashtag2"],
    "accounts": ["account1", "account2"]
}
```

### フロントエンドへの国追加

`frontend/app/admin/scraper/page.tsx` のセレクトボックスに追加：

```tsx
<option value="NewCountry">NewCountry</option>
```

---

*最終更新: 2026-02-08*
