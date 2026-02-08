# スクレイピング設計ドキュメント

Instagram Scraping Systemの国別スクレイピングターゲット設定

> **最終更新**: 2026-02-08
> **バージョン**: 2.0
> **変更内容**: Apify Instagram Hashtag Scraperに移行、セキュリティ強化

---

## 概要

このシステムは、各国の日本人ワーホリ・留学生・駐在員向けに最適化されたInstagram情報を収集します。

### ⚠️ 重要な設計方針

**Job（求人）とHouse（住居）を最優先で収集します。**

#### Apify Instagram Hashtag Scraper への移行

| 変更前 | 変更後 |
|--------|--------|
| `apify~instagram-scraper` | `apify~instagram-hashtag-scraper` |
| directUrls方式 | hashtags配列方式 |
| アカウント+ハッシュタグ混在 | ハッシュタグ検索のみ |

#### なぜ移行したか？

| 理由 | 詳細 |
|------|------|
| **データ取得精度** | Hashtag Scraperは投稿データを直接返却（メタデータのみを返す問題を解消） |
| **多様なソース** | ハッシュタグ検索で多くのアカウントから情報を取得可能 |
| **安定性** | 専用Actorのため安定して動作 |

#### レストランアカウントを削除した理由

| 問題 | 詳細 |
|------|------|
| **料理写真が99%** | レストランの投稿は料理写真がメイン。求人は月1回程度 |
| **プロモーション誤分類** | 「新メニュー」「キャンペーン」がEventと誤分類される |
| **多様性の欠如** | 飲食ばかりで他業種の求人が取れない |

### 処理フロー

```
1. Apify Instagram Hashtag Scraperでハッシュタグから投稿を取得
   ├── 最大5ハッシュタグを検索（COUNTRY_TARGETS[:5]）
   └── Residentialプロキシ使用でブロック回避
           ↓
2. 日付フィルター（14日以内のみ）
           ↓
3. 重複フィルター（DB既存のshortCodeをスキップ）
           ↓
4. Gemini Vision APIでカテゴリ分類
   ├── テキスト解析
   └── 画像内テキスト解析（求人画像に有効）
           ↓
5. 優先順位でソート（Job > House > Event > Ignore）
           ↓
6. Supabaseに保存
```

---

## 技術仕様

### Apify Actor設定

```python
APIFY_ACTOR_ID = "apify~instagram-hashtag-scraper"

actor_input = {
    "hashtags": hashtags[:5],  # 最初の5ハッシュタグを使用
    "resultsLimit": 50,        # ハッシュタグあたり最大50件
    "proxy": {
        "useApifyProxy": True,
        "apifyProxyGroups": ["RESIDENTIAL"]
    }
}
```

### 取得されるデータ構造

```json
{
    "inputUrl": "https://www.instagram.com/explore/tags/torontojobs",
    "id": "3822486619098940385",
    "type": "Image",
    "shortCode": "DUMM1PiE4Ph",
    "caption": "We're hiring! Server position available...",
    "hashtags": ["NowHiring", "TorontoJobs"],
    "url": "https://www.instagram.com/p/DUMM1PiE4Ph/",
    "displayUrl": "https://...",
    "timestamp": "2026-02-05T10:00:00.000Z",
    "ownerUsername": "restaurant_name",
    "likesCount": 42,
    "commentsCount": 3
}
```

---

## 国別ターゲット設定

### 🇨🇦 Toronto (Canada)

#### ハッシュタグ（最初の5つを使用）

| # | ハッシュタグ | 説明 | カテゴリ |
|---|------------|------|----------|
| 1 | `torontojobs` | 求人全般 | Job |
| 2 | `torontohiring` | 採用情報 | Job |
| 3 | `gtajobs` | GTA地域求人 | Job |
| 4 | `torontowork` | 仕事情報 | Job |
| 5 | `hiringtoronto` | 採用中 | Job |

#### 全ハッシュタグ一覧

**求人系（Job）**
- `torontojobs`, `torontohiring`, `gtajobs`, `torontowork`, `hiringtoronto`
- `トロント求人`, `トロント仕事`, `カナダ求人`, `ワーホリ求人`

**住居系（House）**
- `torontorentals`, `torontohousing`, `torontoroommate`
- `トロント賃貸`, `トロントシェアハウス`, `トロント部屋探し`

#### 参考アカウント（現在未使用）

| アカウント | 説明 | 備考 |
|-----------|------|------|
| `@jpcanada_com` | JPCanada掲示板 | ハッシュタグ検索で取得可能 |
| `@eマップル` | e-Maple | ハッシュタグ検索で取得可能 |

---

### 🇹🇭 Thailand

#### ハッシュタグ（最初の5つを使用）

| # | ハッシュタグ | 説明 | カテゴリ |
|---|------------|------|----------|
| 1 | `bangkokjobs` | バンコク求人 | Job |
| 2 | `thailandjobs` | タイ求人 | Job |
| 3 | `タイ求人` | 日本語求人 | Job |
| 4 | `タイ就職` | 就職情報 | Job |
| 5 | `バンコク求人` | バンコク求人 | Job |

#### 全ハッシュタグ一覧

**求人系（Job）**
- `bangkokjobs`, `thailandjobs`, `タイ求人`, `タイ就職`, `バンコク求人`
- `タイ転職`, `タイ駐在`

**住居系（House）**
- `bangkokrentals`, `bangkokcondo`
- `バンコク賃貸`, `バンコクコンドミニアム`, `タイ不動産`

---

### 🇵🇭 Philippines

#### ハッシュタグ（最初の5つを使用）

| # | ハッシュタグ | 説明 | カテゴリ |
|---|------------|------|----------|
| 1 | `フィリピン求人` | 日本語求人 | Job |
| 2 | `セブ求人` | セブ求人 | Job |
| 3 | `マニラ求人` | マニラ求人 | Job |
| 4 | `cebujobs` | セブ求人 | Job |
| 5 | `manilajobs` | マニラ求人 | Job |

#### 全ハッシュタグ一覧

**求人系（Job）**
- `フィリピン求人`, `セブ求人`, `マニラ求人`, `cebujobs`, `manilajobs`
- `philippinesjobs`, `フィリピン就職`

**住居系（House）**
- `ceburentals`, `manilarentals`, `セブ賃貸`

---

### 🇬🇧 UK (イギリス)

#### ハッシュタグ（最初の5つを使用）

| # | ハッシュタグ | 説明 | カテゴリ |
|---|------------|------|----------|
| 1 | `londonjobs` | ロンドン求人 | Job |
| 2 | `ukhiring` | UK採用 | Job |
| 3 | `londonhiring` | ロンドン採用 | Job |
| 4 | `ukjobs` | UK求人 | Job |
| 5 | `ロンドン求人` | 日本語求人 | Job |

#### 全ハッシュタグ一覧

**求人系（Job）**
- `londonjobs`, `ukhiring`, `londonhiring`, `ukjobs`
- `ロンドン求人`, `イギリス求人`, `イギリスワーホリ求人`, `ロンドン仕事`

**住居系（House）**
- `londonrentals`, `londonroomshare`, `londonflat`
- `ロンドン賃貸`, `ロンドンシェアハウス`

---

### 🇦🇺 Australia

#### ハッシュタグ（最初の5つを使用）

| # | ハッシュタグ | 説明 | カテゴリ |
|---|------------|------|----------|
| 1 | `sydneyjobs` | シドニー求人 | Job |
| 2 | `melbournejobs` | メルボルン求人 | Job |
| 3 | `australiajobs` | オーストラリア求人 | Job |
| 4 | `オーストラリア求人` | 日本語求人 | Job |
| 5 | `シドニー求人` | シドニー求人 | Job |

#### 全ハッシュタグ一覧

**求人系（Job）**
- `sydneyjobs`, `melbournejobs`, `australiajobs`
- `オーストラリア求人`, `シドニー求人`, `メルボルン求人`
- `ワーホリオーストラリア`, `オーストラリアワーホリ求人`

**住居系（House）**
- `sydneyrentals`, `melbournerentals`
- `シドニー賃貸`, `メルボルン賃貸`, `シドニーシェアハウス`

---

## 削除されたターゲット

### レストランアカウント（全削除）

| アカウント | 削除理由 |
|-----------|---------|
| `@gyukaku` | 料理写真が99%、求人は稀 |
| `@sansoteiramen` | 料理写真が99%、求人は稀 |
| `@kibosushi_official` | 料理写真が99%、求人は稀 |
| `@hibachicanada` | 料理写真が99%、求人は稀 |
| `@jinya_ramen` | 料理写真が99%、求人は稀 |
| `@ichirancanada` | 料理写真が99%、求人は稀 |
| `@izakayadomo` | 料理写真が99%、求人は稀 |

### イベント系アカウント

| アカウント | 削除理由 |
|-----------|---------|
| `@blogto` | ニュース・イベント中心 |
| `@torontolife` | ライフスタイル・イベント多い |
| `@japanhouseld` | 文化・イベント情報 |

---

## AI分類ルール

### 優先順位

```
Job 💼 > House 🏠 > Event 🎉 > Ignore 🚫
```

### 厳格なIgnore判定

以下は**必ずIgnore**に分類されます：

| 内容 | 理由 |
|------|------|
| 料理写真（ラーメン、寿司、etc） | 求人/住居に無関係 |
| レストランプロモーション | 「新メニュー」「期間限定」「キャンペーン」 |
| 店舗ニュース（求人なし） | 「オープンしました」「営業時間変更」 |
| パーソナル投稿 | 旅行写真、日常写真 |

### Eventの厳格な条件

Eventと分類されるには**全て**が必要：
- ✅ 明確なイベント名
- ✅ 具体的な日時
- ✅ 公共の場所/会場
- ✅ コミュニティ向けの公開イベント

**以下はEvent ではなく Ignore**：
- ❌ レストランの特別メニュー
- ❌ ハッピーアワー
- ❌ 店舗オープニング
- ❌ 割引キャンペーン

---

## フィルター設定

| 項目 | 値 | 説明 |
|---|---|---|
| 日付フィルター | 14日 | 14日以上前の投稿はスキップ |
| 重複フィルター | ON | DB既存のshortCodeはスキップ |
| ハッシュタグ上限 | 5個 | 最初の5ハッシュタグのみ使用 |
| 取得上限/ハッシュタグ | 50件 | 各ハッシュタグから最大50件取得 |
| 処理上限 | 10件 | 1回の実行で最大10件をAI解析 |

---

## セキュリティ対策

### APIエンドポイント（/api/scrape）

| 対策 | 内容 |
|------|------|
| **ホワイトリスト検証** | country は許可された5か国のみ |
| **数値バリデーション** | days: 1-365, limit: 1-50 の範囲制限 |
| **コマンドインジェクション防止** | シェルコマンドに直接入力を渡さない |

```typescript
const ALLOWED_COUNTRIES = ['Toronto', 'Thailand', 'Philippines', 'UK', 'Australia'];
const safeCountry = ALLOWED_COUNTRIES.includes(country) ? country : 'Toronto';
```

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-02-08 | Apify Instagram Hashtag Scraper に移行 |
| 2026-02-08 | セキュリティ対策（コマンドインジェクション防止）追加 |
| 2026-02-08 | 技術仕様セクション追加 |
| 2026-02-08 | レストランアカウントを全削除 |
| 2026-02-08 | ハッシュタグ検索を大幅増強 |
| 2026-02-08 | AIプロンプト強化（飲食プロモーション→Ignore） |
| 2026-02-08 | コミュニティ掲示板アカウントに集中 |
