"""Domain-organized vocabulary networks for Japanese learning.

Each domain contains thematically related vocabulary organized as a network
with center words, related words, example sentences, and grammar points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class VocabWord:
    """A single vocabulary word with full annotation data."""
    word: str
    reading: str
    meaning: str
    level: str = "N5"
    pos: str = ""
    example_jp: str = ""
    example_zh: str = ""
    example_reading: str = ""
    related: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "reading": self.reading,
            "meaning": self.meaning,
            "level": self.level,
            "pos": self.pos,
            "example_jp": self.example_jp,
            "example_zh": self.example_zh,
            "example_reading": self.example_reading,
            "related": self.related,
            "tags": self.tags,
        }


@dataclass
class VocabNetwork:
    """A network of related vocabulary around a domain center."""
    domain_id: str
    domain_name: str
    domain_name_ja: str
    description: str = ""
    center_words: List[str] = field(default_factory=list)
    words: List[VocabWord] = field(default_factory=list)
    grammar_points: List[Dict] = field(default_factory=list)
    language: str = "ja"
    """Study language code this network belongs to (ja/zh/en/...)."""

    def to_dict(self) -> dict:
        return {
            "domain_id": self.domain_id,
            "domain_name": self.domain_name,
            "domain_name_ja": self.domain_name_ja,
            "description": self.description,
            "center_words": self.center_words,
            "words": [w.to_dict() for w in self.words],
            "grammar_points": self.grammar_points,
            "language": self.language,
        }


VOCAB_NETWORKS: Dict[str, VocabNetwork] = {}


def _register(network: VocabNetwork):
    VOCAB_NETWORKS[network.domain_id] = network
    return network


# ═══════════════════════════════════════════════════════════════
# 计算机 / Computer & IT
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="computer",
    domain_name="计算机与信息技术",
    domain_name_ja="コンピュータ・IT",
    description="计算机硬件、软件、编程、网络等相关词汇的网络",
    center_words=["コンピュータ", "プログラム", "インターネット"],
    words=[
        VocabWord(word="コンピュータ", reading="こんぴゅーた", meaning="计算机", level="N4", pos="名詞",
                  example_jp="コンピュータを使ってレポートを書く。", example_zh="用计算机写报告。",
                  example_reading="こんぴゅーたをつかってれぽーとをかく", related=["パソコン", "プログラム"]),
        VocabWord(word="パソコン", reading="ぱそこん", meaning="个人电脑", level="N4", pos="名詞",
                  example_jp="パソコンでメールを送る。", example_zh="用个人电脑发邮件。",
                  example_reading="ぱそこんでめーるをおくる", related=["コンピュータ", "インターネット"]),
        VocabWord(word="プログラム", reading="ぷろぐらむ", meaning="程序", level="N3", pos="名詞",
                  example_jp="プログラムを作成する。", example_zh="编写程序。",
                  example_reading="ぷろぐらむをさくせいする", related=["プログラミング", "ソフトウェア"]),
        VocabWord(word="プログラミング", reading="ぷろぐらみんぐ", meaning="编程", level="N3", pos="名詞",
                  example_jp="プログラミングを学ぶ。", example_zh="学习编程。",
                  example_reading="ぷろぐらみんぐをまなぶ", related=["プログラム", "コード"]),
        VocabWord(word="ソフトウェア", reading="そふとうぇあ", meaning="软件", level="N3", pos="名詞",
                  example_jp="このソフトウェアは無料だ。", example_zh="这个软件是免费的。",
                  example_reading="このそふとうぇあはむりょうだ", related=["ハードウェア", "アプリ"]),
        VocabWord(word="ハードウェア", reading="はーどうぇあ", meaning="硬件", level="N2", pos="名詞",
                  example_jp="ハードウェアの故障を修理する。", example_zh="修理硬件故障。",
                  example_reading="はーどうぇあのこしょうをしゅうりする", related=["ソフトウェア", "パソコン"]),
        VocabWord(word="インターネット", reading="いんたーねっと", meaning="互联网", level="N4", pos="名詞",
                  example_jp="インターネットで情報を調べる。", example_zh="在互联网上查资料。",
                  example_reading="いんたーねっとでじょうほうをしらべる", related=["ウェブ", "メール"]),
        VocabWord(word="ウェブサイト", reading="うぇぶさいと", meaning="网站", level="N3", pos="名詞",
                  example_jp="会社のウェブサイトを作る。", example_zh="制作公司网站。",
                  example_reading="かいしゃのうぇぶさいとをつくる", related=["インターネット", "リンク"]),
        VocabWord(word="データ", reading="でーた", meaning="数据", level="N3", pos="名詞",
                  example_jp="データを保存する。", example_zh="保存数据。",
                  example_reading="でーたをほぞんする", related=["ファイル", "サーバー"]),
        VocabWord(word="ファイル", reading="ふぁいる", meaning="文件", level="N3", pos="名詞",
                  example_jp="ファイルをダウンロードする。", example_zh="下载文件。",
                  example_reading="ふぁいるをだうんろーどする", related=["データ", "フォルダ"]),
        VocabWord(word="アプリ", reading="あぷり", meaning="应用程序", level="N4", pos="名詞",
                  example_jp="このアプリは便利だ。", example_zh="这个应用很方便。",
                  example_reading="このあぷりはべんりだ", related=["ソフトウェア", "スマホ"]),
        VocabWord(word="スマホ", reading="すまほ", meaning="智能手机", level="N4", pos="名詞",
                  example_jp="スマホで写真を撮る。", example_zh="用智能手机拍照。",
                  example_reading="すまほでしゃしんをとる", related=["アプリ", "メール"]),
        VocabWord(word="メール", reading="めーる", meaning="邮件", level="N4", pos="名詞",
                  example_jp="メールを送る。", example_zh="发邮件。",
                  example_reading="めーるをおくる", related=["インターネット", "スマホ"]),
        VocabWord(word="コード", reading="こーど", meaning="代码", level="N3", pos="名詞",
                  example_jp="ソースコードを書く。", example_zh="写源代码。",
                  example_reading="そーすこーどをかく", related=["プログラム", "プログラミング"]),
        VocabWord(word="サーバー", reading="さーばー", meaning="服务器", level="N2", pos="名詞",
                  example_jp="サーバーにデータを保存する。", example_zh="把数据保存在服务器上。",
                  example_reading="さーばーにでーたをほぞんする", related=["データ", "ネットワーク"]),
        VocabWord(word="ネットワーク", reading="ねっとわーく", meaning="网络", level="N2", pos="名詞",
                  example_jp="ネットワークの設定を変える。", example_zh="更改网络设置。",
                  example_reading="ねっとわーくのせっていをかえる", related=["インターネット", "サーバー"]),
        VocabWord(word="画面", reading="がめん", meaning="画面/屏幕", level="N4", pos="名詞",
                  example_jp="画面が見えない。", example_zh="看不清屏幕。",
                  example_reading="がめんがみえない", related=["パソコン", "スマホ"]),
        VocabWord(word="入力", reading="にゅうりょく", meaning="输入", level="N3", pos="名詞",
                  example_jp="パスワードを入力する。", example_zh="输入密码。",
                  example_reading="ぱすわーどをにゅうりょくする", related=["データ", "キーボード"]),
        VocabWord(word="出力", reading="しゅつりょく", meaning="输出", level="N3", pos="名詞",
                  example_jp="ファイルを出力する。", example_zh="导出文件。",
                  example_reading="ふぁいるをしゅつりょくする", related=["入力", "データ"]),
        VocabWord(word="検索", reading="けんさく", meaning="检索/搜索", level="N3", pos="名詞",
                  example_jp="インターネットで検索する。", example_zh="在互联网上搜索。",
                  example_reading="いんたーねっとでけんさくする", related=["インターネット", "ウェブサイト"]),
        VocabWord(word="ダウンロード", reading="だうんろーど", meaning="下载", level="N3", pos="名詞",
                  example_jp="アプリをダウンロードする。", example_zh="下载应用。",
                  example_reading="あぷりをだうんろーどする", related=["ファイル", "ソフトウェア"]),
        VocabWord(word="アップロード", reading="あっぷろーど", meaning="上传", level="N3", pos="名詞",
                  example_jp="写真をアップロードする。", example_zh="上传照片。",
                  example_reading="しゃしんをあっぷろーどする", related=["ダウンロード", "データ"]),
        VocabWord(word="保存", reading="ほぞん", meaning="保存", level="N4", pos="名詞/サ変",
                  example_jp="ファイルを保存する。", example_zh="保存文件。",
                  example_reading="ふぁいるをほぞんする", related=["データ", "ファイル"]),
        VocabWord(word="削除", reading="さくじょ", meaning="删除", level="N3", pos="名詞/サ変",
                  example_jp="不要なファイルを削除する。", example_zh="删除不需要的文件。",
                  example_reading="ふようなふぁいるをさくじょする", related=["保存", "データ"]),
    ],
    grammar_points=[
        {"pattern": "〜を使（つか）って", "meaning": "使用…来…", "example": "コンピュータを使ってレポートを書く。", "level": "N4"},
        {"pattern": "〜で（手段）", "meaning": "用…（手段）", "example": "スマホで写真を撮る。", "level": "N4"},
        {"pattern": "〜を入力する", "meaning": "输入…", "example": "パスワードを入力する。", "level": "N3"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 写真・カメラ / Photography
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="photography",
    domain_name="摄影",
    domain_name_ja="写真・カメラ",
    description="摄影、相机、拍摄技术等相关词汇的网络",
    center_words=["写真", "カメラ", "レンズ"],
    words=[
        VocabWord(word="写真", reading="しゃしん", meaning="照片", level="N5", pos="名詞",
                  example_jp="写真を撮る。", example_zh="拍照。",
                  example_reading="しゃしんをとる", related=["カメラ", "レンズ"]),
        VocabWord(word="カメラ", reading="かめら", meaning="相机", level="N4", pos="名詞",
                  example_jp="新しいカメラを買った。", example_zh="买了新相机。",
                  example_reading="あたらしいかめらをかった", related=["写真", "レンズ"]),
        VocabWord(word="レンズ", reading="れんず", meaning="镜头", level="N2", pos="名詞",
                  example_jp="レンズを交換する。", example_zh="更换镜头。",
                  example_reading="れんずをこうかんする", related=["カメラ", "焦点"]),
        VocabWord(word="撮る", reading="とる", meaning="拍摄", level="N5", pos="動詞",
                  example_jp="記念写真を撮る。", example_zh="拍纪念照。",
                  example_reading="きねんしゃしんをとる", related=["写真", "カメラ"]),
        VocabWord(word="風景", reading="ふうけい", meaning="风景", level="N3", pos="名詞",
                  example_jp="きれいな風景を写真に撮る。", example_zh="把美丽的风景拍下来。",
                  example_reading="きれいなふうけいをしゃしんにとる", related=["写真", "自然"]),
        VocabWord(word="景色", reading="けしき", meaning="景色", level="N3", pos="名詞",
                  example_jp="山の上からの景色はすばらしい。", example_zh="从山顶看到的景色很壮观。",
                  example_reading="やまのうえからのけしきはすばらしい", related=["風景", "自然"]),
        VocabWord(word="露出", reading="ろしゅつ", meaning="曝光", level="N1", pos="名詞",
                  example_jp="露出を調整する。", example_zh="调整曝光。",
                  example_reading="ろしゅつをちょうせいする", related=["カメラ", "レンズ"]),
        VocabWord(word="焦点", reading="しょうてん", meaning="焦点/对焦", level="N2", pos="名詞",
                  example_jp="焦点を合わせる。", example_zh="对焦。",
                  example_reading="しょうてんをあわせる", related=["レンズ", "カメラ"]),
        VocabWord(word="絞り", reading="しぼり", meaning="光圈", level="N1", pos="名詞",
                  example_jp="絞りを開放する。", example_zh="开大光圈。",
                  example_reading="しぼりをかいほうする", related=["露出", "レンズ"]),
        VocabWord(word="シャッター", reading="しゃったー", meaning="快门", level="N2", pos="名詞",
                  example_jp="シャッターを切る。", example_zh="按快门。",
                  example_reading="しゃったーをきる", related=["カメラ", "写真"]),
        VocabWord(word="フラッシュ", reading="ふらっしゅ", meaning="闪光灯", level="N3", pos="名詞",
                  example_jp="フラッシュを使わないで撮る。", example_zh="不用闪光灯拍。",
                  example_reading="ふらっしゅをつかわないでとる", related=["カメラ", "写真"]),
        VocabWord(word="フィルム", reading="ふぃるむ", meaning="胶片", level="N2", pos="名詞",
                  example_jp="フィルムカメラが好きだ。", example_zh="喜欢胶片相机。",
                  example_reading="ふぃるむかめらがすきだ", related=["カメラ", "写真"]),
        VocabWord(word="三脚", reading="さんきゃく", meaning="三脚架", level="N2", pos="名詞",
                  example_jp="三脚にカメラを固定する。", example_zh="把相机固定在三脚架上。",
                  example_reading="さんきゃくにかめらをこていする", related=["カメラ", "撮る"]),
        VocabWord(word="現像", reading="げんぞう", meaning="冲洗/显影", level="N1", pos="名詞/サ変",
                  example_jp="写真を現像する。", example_zh="冲洗照片。",
                  example_reading="しゃしんをげんぞうする", related=["写真", "フィルム"]),
        VocabWord(word="逆光", reading="ぎゃっこう", meaning="逆光", level="N1", pos="名詞",
                  example_jp="逆光で写真を撮る。", example_zh="逆光拍照。",
                  example_reading="ぎゃっこうでしゃしんをとる", related=["露出", "光"]),
        VocabWord(word="構図", reading="こうず", meaning="构图", level="N1", pos="名詞",
                  example_jp="構図を考える。", example_zh="考虑构图。",
                  example_reading="こうずをかんがえる", related=["写真", "美術"]),
        VocabWord(word="背景", reading="はいけい", meaning="背景", level="N3", pos="名詞",
                  example_jp="背景がぼやけている。", example_zh="背景模糊了。",
                  example_reading="はいけいがぼやけている", related=["構図", "写真"]),
        VocabWord(word="光", reading="ひかり", meaning="光", level="N4", pos="名詞",
                  example_jp="光がきれいだ。", example_zh="光线很美。",
                  example_reading="ひかりがきれいだ", related=["露出", "逆光"]),
    ],
    grammar_points=[
        {"pattern": "〜を撮（と）る", "meaning": "拍…", "example": "写真を撮る。", "level": "N5"},
        {"pattern": "〜に固定（こてい）する", "meaning": "固定在…上", "example": "三脚にカメラを固定する。", "level": "N2"},
        {"pattern": "〜ないで撮る", "meaning": "不…而拍", "example": "フラッシュを使わないで撮る。", "level": "N4"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 芸術 / Art
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="art",
    domain_name="艺术",
    domain_name_ja="芸術",
    description="绘画、雕塑、设计等艺术相关词汇的网络",
    center_words=["芸術", "絵", "美術"],
    words=[
        VocabWord(word="芸術", reading="げいじゅつ", meaning="艺术", level="N3", pos="名詞",
                  example_jp="芸術は世界共通の言語だ。", example_zh="艺术是世界共通的语言。",
                  example_reading="げいじゅつはせかいきょうつうのげんごだ", related=["美術", "絵"]),
        VocabWord(word="絵", reading="え", meaning="画/绘画", level="N5", pos="名詞",
                  example_jp="絵を描く。", example_zh="画画。",
                  example_reading="えをかく", related=["美術", "画家"]),
        VocabWord(word="美術", reading="びじゅつ", meaning="美术", level="N4", pos="名詞",
                  example_jp="美術館に行く。", example_zh="去美术馆。",
                  example_reading="びじゅつかんにいく", related=["芸術", "絵"]),
        VocabWord(word="画家", reading="がか", meaning="画家", level="N3", pos="名詞",
                  example_jp="あの画家の作品が好きだ。", example_zh="喜欢那位画家的作品。",
                  example_reading="あのがかのさくひんがすきだ", related=["絵", "美術"]),
        VocabWord(word="描く", reading="かく", meaning="画/描绘", level="N4", pos="動詞",
                  example_jp="風景を描く。", example_zh="画风景。",
                  example_reading="ふうけいをかく", related=["絵", "画家"]),
        VocabWord(word="色", reading="いろ", meaning="颜色", level="N5", pos="名詞",
                  example_jp="好きな色は何ですか。", example_zh="你喜欢什么颜色？",
                  example_reading="すきないろはなんですか", related=["絵", "赤"]),
        VocabWord(word="赤", reading="あか", meaning="红色", level="N5", pos="名詞/形容詞",
                  example_jp="赤い花が咲いている。", example_zh="红花开了。",
                  example_reading="あかいはながさいている", related=["色", "青"]),
        VocabWord(word="青", reading="あお", meaning="蓝色", level="N5", pos="名詞/形容詞",
                  example_jp="空が青い。", example_zh="天空是蓝色的。",
                  example_reading="そらがあおい", related=["色", "赤"]),
        VocabWord(word="白", reading="しろ", meaning="白色", level="N5", pos="名詞/形容詞",
                  example_jp="白い紙に絵を描く。", example_zh="在白纸上画画。",
                  example_reading="しろいかみにえをかく", related=["色", "黒"]),
        VocabWord(word="黒", reading="くろ", meaning="黑色", level="N5", pos="名詞/形容詞",
                  example_jp="黒いインクで書く。", example_zh="用黑墨水写。",
                  example_reading="くろいいんくでかく", related=["色", "白"]),
        VocabWord(word="作品", reading="さくひん", meaning="作品", level="N3", pos="名詞",
                  example_jp="この作品は19世紀のものだ。", example_zh="这幅作品是19世纪的。",
                  example_reading="このさくひんはじゅうきせいきのものだ", related=["芸術", "画家"]),
        VocabWord(word="展覧会", reading="てんらんかい", meaning="展览会", level="N2", pos="名詞",
                  example_jp="展覧会に行く。", example_zh="去看展览。",
                  example_reading="てんらんかいにいく", related=["美術", "作品"]),
        VocabWord(word="美術館", reading="びじゅつかん", meaning="美术馆", level="N3", pos="名詞",
                  example_jp="美術館で絵を見る。", example_zh="在美术馆看画。",
                  example_reading="びじゅつかんでえをみる", related=["芸術", "展覧会"]),
        VocabWord(word="彫刻", reading="ちょうこく", meaning="雕刻/雕塑", level="N2", pos="名詞",
                  example_jp="彫刻を鑑賞する。", example_zh="鉴赏雕刻。",
                  example_reading="ちょうこくをかんしょうする", related=["芸術", "作品"]),
        VocabWord(word="デザイン", reading="でざいん", meaning="设计", level="N3", pos="名詞",
                  example_jp="新しいデザインを考える。", example_zh="考虑新设计。",
                  example_reading="あたらしいでざいんをかんがえる", related=["芸術", "美術"]),
        VocabWord(word="創作", reading="そうさく", meaning="创作", level="N2", pos="名詞/サ変",
                  example_jp="芸術作品を創作する。", example_zh="创作艺术作品。",
                  example_reading="げいじゅつさくひんをそうさくする", related=["作品", "芸術"]),
        VocabWord(word="鑑賞", reading="かんしょう", meaning="鉴赏/欣赏", level="N1", pos="名詞/サ変",
                  example_jp="美術作品を鑑賞する。", example_zh="鉴赏美术作品。",
                  example_reading="びじゅつさくひんをかんしょうする", related=["美術", "展覧会"]),
        VocabWord(word="印象", reading="いんしょう", meaning="印象", level="N3", pos="名詞",
                  example_jp="深い印象を受けた。", example_zh="受到了深刻的印象。",
                  example_reading="ふかいいんしょうをうけた", related=["作品", "芸術"]),
        VocabWord(word="表現", reading="ひょうげん", meaning="表现/表达", level="N3", pos="名詞/サ変",
                  example_jp="感情を表現する。", example_zh="表达感情。",
                  example_reading="かんじょうをひょうげんする", related=["芸術", "創作"]),
    ],
    grammar_points=[
        {"pattern": "〜で描（か）く", "meaning": "用…画", "example": "水彩で絵を描く。", "level": "N4"},
        {"pattern": "〜に見（み）える", "meaning": "看起来像…", "example": "この絵は古く見える。", "level": "N3"},
        {"pattern": "〜を受（う）ける", "meaning": "受到…", "example": "深い印象を受けた。", "level": "N3"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 音楽 / Music
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="music",
    domain_name="音乐",
    domain_name_ja="音楽",
    description="乐器、演奏、音乐类型等相关词汇的网络",
    center_words=["音楽", "歌", "ピアノ"],
    words=[
        VocabWord(word="音楽", reading="おんがく", meaning="音乐", level="N4", pos="名詞",
                  example_jp="音楽を聞くのが好きだ。", example_zh="喜欢听音乐。",
                  example_reading="おんがくをきくのがすきだ", related=["歌", "ピアノ"]),
        VocabWord(word="歌", reading="うた", meaning="歌/歌曲", level="N5", pos="名詞",
                  example_jp="歌を歌う。", example_zh="唱歌。",
                  example_reading="うたをうたう", related=["音楽", "歌手"]),
        VocabWord(word="歌う", reading="うたう", meaning="唱", level="N4", pos="動詞",
                  example_jp="友達と一緒に歌う。", example_zh="和朋友一起唱歌。",
                  example_reading="ともだちといっしょにうたう", related=["歌", "音楽"]),
        VocabWord(word="ピアノ", reading="ぴあの", meaning="钢琴", level="N4", pos="名詞",
                  example_jp="ピアノを弾く。", example_zh="弹钢琴。",
                  example_reading="ぴあのをひく", related=["音楽", "弾く"]),
        VocabWord(word="ギター", reading="ぎたー", meaning="吉他", level="N3", pos="名詞",
                  example_jp="ギターを弾く。", example_zh="弹吉他。",
                  example_reading="ぎたーをひく", related=["音楽", "ピアノ"]),
        VocabWord(word="弾く", reading="ひく", meaning="弹（乐器）", level="N4", pos="動詞",
                  example_jp="ピアノを弾く。", example_zh="弹钢琴。",
                  example_reading="ぴあのをひく", related=["ピアノ", "ギター"]),
        VocabWord(word="聞く", reading="きく", meaning="听", level="N5", pos="動詞",
                  example_jp="音楽を聞く。", example_zh="听音乐。",
                  example_reading="おんがくをきく", related=["音楽", "歌"]),
        VocabWord(word="演奏", reading="えんそう", meaning="演奏", level="N3", pos="名詞/サ変",
                  example_jp="オーケストラの演奏を聞く。", example_zh="听管弦乐队演奏。",
                  example_reading="おーけすとらのえんそうをきく", related=["音楽", "ピアノ"]),
        VocabWord(word="歌手", reading="かしゅ", meaning="歌手", level="N3", pos="名詞",
                  example_jp="あの歌手は人気がある。", example_zh="那位歌手很受欢迎。",
                  example_reading="あのかしゅはにんきがある", related=["歌", "音楽"]),
        VocabWord(word="作曲", reading="さっきょく", meaning="作曲", level="N2", pos="名詞/サ変",
                  example_jp="曲を作曲する。", example_zh="作曲。",
                  example_reading="きょくをさっきょくする", related=["音楽", "演奏"]),
        VocabWord(word="旋律", reading="せんりつ", meaning="旋律", level="N1", pos="名詞",
                  example_jp="美しい旋律だ。", example_zh="优美的旋律。",
                  example_reading="うつくしいせんりつだ", related=["音楽", "作曲"]),
        VocabWord(word="拍子", reading="びょうし", meaning="节拍", level="N2", pos="名詞",
                  example_jp="拍子に合わせて歌う。", example_zh="合着节拍唱歌。",
                  example_reading="びょうしにあわせてうたう", related=["音楽", "歌"]),
        VocabWord(word="リズム", reading="りずむ", meaning="节奏", level="N3", pos="名詞",
                  example_jp="リズムに乗って踊る。", example_zh="跟着节奏跳舞。",
                  example_reading="りずむにのっておどる", related=["音楽", "拍子"]),
        VocabWord(word="コンサート", reading="こんさーと", meaning="音乐会", level="N3", pos="名詞",
                  example_jp="コンサートに行く。", example_zh="去听音乐会。",
                  example_reading="こんさーとにいく", related=["音楽", "演奏"]),
        VocabWord(word="楽器", reading="がっき", meaning="乐器", level="N3", pos="名詞",
                  example_jp="何か楽器を演奏しますか。", example_zh="你会演奏什么乐器吗？",
                  example_reading="なにかがっきをえんそうしますか", related=["ピアノ", "ギター"]),
    ],
    grammar_points=[
        {"pattern": "〜を弾（ひ）く", "meaning": "弹（乐器）", "example": "ピアノを弾く。", "level": "N4"},
        {"pattern": "〜が好きだ", "meaning": "喜欢…", "example": "音楽を聞くのが好きだ。", "level": "N5"},
        {"pattern": "〜に合（あ）わせて", "meaning": "合着…", "example": "拍子に合わせて歌う。", "level": "N2"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 料理 / Cooking & Food
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="cooking",
    domain_name="烹饪与美食",
    domain_name_ja="料理・食べ物",
    description="食材、烹饪方法、料理类型等相关词汇的网络",
    center_words=["料理", "食べ物", "味"],
    words=[
        VocabWord(word="料理", reading="りょうり", meaning="料理/烹饪", level="N4", pos="名詞/サ変",
                  example_jp="日本料理を作る。", example_zh="做日本料理。",
                  example_reading="にほんりょうりをつくる", related=["食べ物", "味"]),
        VocabWord(word="食べ物", reading="たべもの", meaning="食物", level="N5", pos="名詞",
                  example_jp="好きな食べ物は何ですか。", example_zh="你喜欢的食物是什么？",
                  example_reading="すきなたべものはなんですか", related=["料理", "味"]),
        VocabWord(word="味", reading="あじ", meaning="味道", level="N4", pos="名詞",
                  example_jp="この料理は味がいい。", example_zh="这道菜味道好。",
                  example_reading="このりょうりはあじがいい", related=["料理", "美味"]),
        VocabWord(word="美味しい", reading="おいしい", meaning="好吃的", level="N5", pos="形容詞",
                  example_jp="この料理は美味しい。", example_zh="这道菜很好吃。",
                  example_reading="このりょうりはおいしい", related=["味", "料理"]),
        VocabWord(word="甘い", reading="あまい", meaning="甜的", level="N5", pos="形容詞",
                  example_jp="このケーキは甘い。", example_zh="这个蛋糕很甜。",
                  example_reading="このけーきはあまい", related=["味", "苦い"]),
        VocabWord(word="辛い", reading="からい", meaning="辣的", level="N4", pos="形容詞",
                  example_jp="韓国料理は辛い。", example_zh="韩国料理很辣。",
                  example_reading="かんこくりょうりはからい", related=["味", "美味しい"]),
        VocabWord(word="苦い", reading="にがい", meaning="苦的", level="N4", pos="形容詞",
                  example_jp="コーヒーは苦い。", example_zh="咖啡是苦的。",
                  example_reading="こーひーはにがい", related=["味", "甘い"]),
        VocabWord(word="焼く", reading="やく", meaning="烤/煎", level="N4", pos="動詞",
                  example_jp="肉を焼く。", example_zh="烤肉。",
                  example_reading="にくをやく", related=["料理", "魚"]),
        VocabWord(word="煮る", reading="にる", meaning="煮", level="N4", pos="動詞",
                  example_jp="野菜を煮る。", example_zh="煮蔬菜。",
                  example_reading="やさいをにる", related=["料理", "スープ"]),
        VocabWord(word="炒める", reading="いためる", meaning="炒", level="N3", pos="動詞",
                  example_jp="野菜を炒める。", example_zh="炒蔬菜。",
                  example_reading="やさいをいためる", related=["料理", "油"]),
        VocabWord(word="切る", reading="きる", meaning="切", level="N4", pos="動詞",
                  example_jp="野菜を切る。", example_zh="切蔬菜。",
                  example_reading="やさいをきる", related=["料理", "包丁"]),
        VocabWord(word="包丁", reading="ほうちょう", meaning="菜刀", level="N2", pos="名詞",
                  example_jp="包丁で魚を切る。", example_zh="用菜刀切鱼。",
                  example_reading="ほうちょうでさかなをきる", related=["料理", "切る"]),
        VocabWord(word="魚", reading="さかな", meaning="鱼", level="N5", pos="名詞",
                  example_jp="新鮮な魚を買う。", example_zh="买新鲜的鱼。",
                  example_reading="しんせんなさかなをかう", related=["料理", "焼く"]),
        VocabWord(word="肉", reading="にく", meaning="肉", level="N5", pos="名詞",
                  example_jp="肉を焼く。", example_zh="烤肉。",
                  example_reading="にくをやく", related=["料理", "焼く"]),
        VocabWord(word="野菜", reading="やさい", meaning="蔬菜", level="N4", pos="名詞",
                  example_jp="野菜をたくさん食べる。", example_zh="吃很多蔬菜。",
                  example_reading="やさいをたくさんたべる", related=["料理", "切る"]),
        VocabWord(word="スープ", reading="すーぷ", meaning="汤", level="N4", pos="名詞",
                  example_jp="温かいスープを飲む。", example_zh="喝热汤。",
                  example_reading="あたたかいすーぷをのむ", related=["料理", "煮る"]),
        VocabWord(word="油", reading="あぶら", meaning="油", level="N3", pos="名詞",
                  example_jp="油で炒める。", example_zh="用油炒。",
                  example_reading="あぶらでいためる", related=["炒める", "料理"]),
        VocabWord(word="食卓", reading="しょくたく", meaning="餐桌", level="N2", pos="名詞",
                  example_jp="食卓を整える。", example_zh="摆餐桌。",
                  example_reading="しょくたくをととのえる", related=["料理", "食べ物"]),
        VocabWord(word="食事", reading="しょくじ", meaning="饭/用餐", level="N4", pos="名詞",
                  example_jp="食事の前に手を洗う。", example_zh="饭前洗手。",
                  example_reading="しょくじのまえにてをあらう", related=["料理", "食べ物"]),
    ],
    grammar_points=[
        {"pattern": "〜を煮（に）る", "meaning": "煮…", "example": "野菜を煮る。", "level": "N4"},
        {"pattern": "〜で炒（いた）める", "meaning": "用…炒", "example": "油で炒める。", "level": "N3"},
        {"pattern": "〜の前に（まえに）", "meaning": "在…之前", "example": "食事の前に手を洗う。", "level": "N4"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 自然 / Nature
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="nature",
    domain_name="自然",
    domain_name_ja="自然",
    description="自然、天气、季节、地理等相关词汇的网络",
    center_words=["自然", "天気", "季節"],
    words=[
        VocabWord(word="自然", reading="しぜん", meaning="自然", level="N3", pos="名詞",
                  example_jp="自然が好きだ。", example_zh="喜欢大自然。",
                  example_reading="しぜんがすきだ", related=["山", "川"]),
        VocabWord(word="天気", reading="てんき", meaning="天气", level="N5", pos="名詞",
                  example_jp="今日は天気がいい。", example_zh="今天天气好。",
                  example_reading="きょうはてんきがいい", related=["雨", "晴れ"]),
        VocabWord(word="季節", reading="きせつ", meaning="季节", level="N3", pos="名詞",
                  example_jp="四季がある。", example_zh="有四个季节。",
                  example_reading="しきがある", related=["春", "夏"]),
        VocabWord(word="春", reading="はる", meaning="春天", level="N5", pos="名詞",
                  example_jp="春にお花見に行く。", example_zh="春天去赏花。",
                  example_reading="はるにおはなみにいく", related=["季節", "桜"]),
        VocabWord(word="夏", reading="なつ", meaning="夏天", level="N5", pos="名詞",
                  example_jp="夏は暑い。", example_zh="夏天很热。",
                  example_reading="なつはあつい", related=["季節", "海"]),
        VocabWord(word="秋", reading="あき", meaning="秋天", level="N5", pos="名詞",
                  example_jp="秋は紅葉がきれいだ。", example_zh="秋天红叶很美。",
                  example_reading="あきはもみじがきれいだ", related=["季節", "紅葉"]),
        VocabWord(word="冬", reading="ふゆ", meaning="冬天", level="N5", pos="名詞",
                  example_jp="冬は寒い。", example_zh="冬天很冷。",
                  example_reading="ふゆはさむい", related=["季節", "雪"]),
        VocabWord(word="山", reading="やま", meaning="山", level="N5", pos="名詞",
                  example_jp="山に登る。", example_zh="爬山。",
                  example_reading="やまにのぼる", related=["自然", "川"]),
        VocabWord(word="川", reading="かわ", meaning="河", level="N5", pos="名詞",
                  example_jp="川で泳ぐ。", example_zh="在河里游泳。",
                  example_reading="かわでおよぐ", related=["自然", "海"]),
        VocabWord(word="海", reading="うみ", meaning="海", level="N5", pos="名詞",
                  example_jp="海へ行く。", example_zh="去海边。",
                  example_reading="うみへいく", related=["夏", "川"]),
        VocabWord(word="花", reading="はな", meaning="花", level="N5", pos="名詞",
                  example_jp="花が咲いている。", example_zh="花开了。",
                  example_reading="はながさいている", related=["春", "自然"]),
        VocabWord(word="桜", reading="さくら", meaning="樱花", level="N4", pos="名詞",
                  example_jp="桜がきれいに咲いた。", example_zh="樱花开得很美。",
                  example_reading="さくらがきれいにさいた", related=["春", "花"]),
        VocabWord(word="雨", reading="あめ", meaning="雨", level="N5", pos="名詞",
                  example_jp="雨が降っている。", example_zh="在下雨。",
                  example_reading="あめがふっている", related=["天気", "傘"]),
        VocabWord(word="雪", reading="ゆき", meaning="雪", level="N5", pos="名詞",
                  example_jp="雪が降る。", example_zh="下雪。",
                  example_reading="ゆきがふる", related=["冬", "天気"]),
        VocabWord(word="風", reading="かぜ", meaning="风", level="N5", pos="名詞",
                  example_jp="風が強い。", example_zh="风很大。",
                  example_reading="かぜがつよい", related=["天気", "自然"]),
        VocabWord(word="空", reading="そら", meaning="天空", level="N4", pos="名詞",
                  example_jp="空が青い。", example_zh="天空是蓝色的。",
                  example_reading="そらがあおい", related=["天気", "星"]),
        VocabWord(word="星", reading="ほし", meaning="星星", level="N4", pos="名詞",
                  example_jp="夜空に星が見える。", example_zh="夜空中能看到星星。",
                  example_reading="よぞらにほしがみえる", related=["空", "月"]),
        VocabWord(word="月", reading="つき", meaning="月亮", level="N4", pos="名詞",
                  example_jp="満月がきれいだ。", example_zh="满月很美。",
                  example_reading="まんげつがきれいだ", related=["星", "空"]),
        VocabWord(word="紅葉", reading="もみじ", meaning="红叶", level="N3", pos="名詞",
                  example_jp="紅葉を見に行く。", example_zh="去看红叶。",
                  example_reading="もみじをみにいく", related=["秋", "自然"]),
        VocabWord(word="晴れ", reading="はれ", meaning="晴天", level="N5", pos="名詞",
                  example_jp="今日は晴れだ。", example_zh="今天是晴天。",
                  example_reading="きょうははれだ", related=["天気", "雨"]),
    ],
    grammar_points=[
        {"pattern": "〜が降（ふ）る", "meaning": "下…（雨/雪）", "example": "雨が降っている。", "level": "N5"},
        {"pattern": "〜に登（のぼ）る", "meaning": "登上…", "example": "山に登る。", "level": "N4"},
        {"pattern": "〜が咲（さ）く", "meaning": "…开花", "example": "花が咲いている。", "level": "N4"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 日常生活 / Daily Life
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="daily",
    domain_name="日常生活",
    domain_name_ja="日常生活",
    description="日常生活、家庭、工作等基础词汇的网络",
    center_words=["家", "仕事", "友達"],
    words=[
        VocabWord(word="家", reading="いえ/うち", meaning="家/房子", level="N5", pos="名詞",
                  example_jp="家に帰る。", example_zh="回家。",
                  example_reading="いえにかえる", related=["家族", "部屋"]),
        VocabWord(word="仕事", reading="しごと", meaning="工作", level="N5", pos="名詞",
                  example_jp="仕事は楽しい。", example_zh="工作很愉快。",
                  example_reading="しごとはたのしい", related=["会社", "働く"]),
        VocabWord(word="友達", reading="ともだち", meaning="朋友", level="N5", pos="名詞",
                  example_jp="友達と遊ぶ。", example_zh="和朋友玩。",
                  example_reading="ともだちとあそぶ", related=["話す", "会う"]),
        VocabWord(word="家族", reading="かぞく", meaning="家人", level="N4", pos="名詞",
                  example_jp="家族と一緒に食事する。", example_zh="和家人一起吃饭。",
                  example_reading="かぞくといっしょにしょくじする", related=["家", "父"]),
        VocabWord(word="朝", reading="あさ", meaning="早上", level="N5", pos="名詞",
                  example_jp="朝ごはんを食べる。", example_zh="吃早饭。",
                  example_reading="あさごはんをたべる", related=["朝ごはん", "起きる"]),
        VocabWord(word="夜", reading="よる", meaning="晚上", level="N5", pos="名詞",
                  example_jp="夜は静かだ。", example_zh="晚上很安静。",
                  example_reading="よるはしずかだ", related=["晩ごはん", "寝る"]),
        VocabWord(word="学校", reading="がっこう", meaning="学校", level="N5", pos="名詞",
                  example_jp="学校に行く。", example_zh="去学校。",
                  example_reading="がっこうにいく", related=["勉強", "先生"]),
        VocabWord(word="会社", reading="かいしゃ", meaning="公司", level="N4", pos="名詞",
                  example_jp="会社で働く。", example_zh="在公司工作。",
                  example_reading="かいしゃではたらく", related=["仕事", "働く"]),
        VocabWord(word="駅", reading="えき", meaning="车站", level="N4", pos="名詞",
                  example_jp="駅で電車に乗る。", example_zh="在车站坐电车。",
                  example_reading="えきででんしゃにのる", related=["電車", "乗る"]),
        VocabWord(word="電車", reading="でんしゃ", meaning="电车", level="N4", pos="名詞",
                  example_jp="電車に乗る。", example_zh="坐电车。",
                  example_reading="でんしゃにのる", related=["駅", "乗る"]),
        VocabWord(word="食べる", reading="たべる", meaning="吃", level="N5", pos="動詞",
                  example_jp="朝ごはんを食べる。", example_zh="吃早饭。",
                  example_reading="あさごはんをたべる", related=["飲む", "料理"]),
        VocabWord(word="飲む", reading="のむ", meaning="喝", level="N5", pos="動詞",
                  example_jp="水を飲む。", example_zh="喝水。",
                  example_reading="みずをのむ", related=["食べる", "コーヒー"]),
        VocabWord(word="行く", reading="いく", meaning="去", level="N5", pos="動詞",
                  example_jp="学校に行く。", example_zh="去学校。",
                  example_reading="がっこうにいく", related=["来る", "帰る"]),
        VocabWord(word="来る", reading="くる", meaning="来", level="N5", pos="動詞",
                  example_jp="友達が来る。", example_zh="朋友来。",
                  example_reading="ともだちがくる", related=["行く", "会う"]),
        VocabWord(word="帰る", reading="かえる", meaning="回去", level="N5", pos="動詞",
                  example_jp="家に帰る。", example_zh="回家。",
                  example_reading="いえにかえる", related=["行く", "家"]),
        VocabWord(word="話す", reading="はなす", meaning="说话", level="N5", pos="動詞",
                  example_jp="友達と話す。", example_zh="和朋友说话。",
                  example_reading="ともだちとはなす", related=["友達", "聞く"]),
        VocabWord(word="見る", reading="みる", meaning="看", level="N5", pos="動詞",
                  example_jp="テレビを見る。", example_zh="看电视。",
                  example_reading="てれびをみる", related=["聞く", "読む"]),
        VocabWord(word="読む", reading="よむ", meaning="读", level="N5", pos="動詞",
                  example_jp="本を読む。", example_zh="读书。",
                  example_reading="ほんをよむ", related=["書く", "見る"]),
        VocabWord(word="書く", reading="かく", meaning="写", level="N5", pos="動詞",
                  example_jp="手紙を書く。", example_zh="写信。",
                  example_reading="てがみをかく", related=["読む", "勉強"]),
        VocabWord(word="勉強", reading="べんきょう", meaning="学习", level="N5", pos="名詞/サ変",
                  example_jp="日本語を勉強する。", example_zh="学习日语。",
                  example_reading="にほんごをべんきょうする", related=["学校", "読む"]),
    ],
    grammar_points=[
        {"pattern": "〜に行（い）く", "meaning": "去…", "example": "学校に行く。", "level": "N5"},
        {"pattern": "〜と一緒（いっしょ）に", "meaning": "和…一起", "example": "友達と一緒に遊ぶ。", "level": "N4"},
        {"pattern": "〜を食（た）べる", "meaning": "吃…", "example": "朝ごはんを食べる。", "level": "N5"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 医学・健康 / Medical & Health
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="medical",
    domain_name="医学与健康",
    domain_name_ja="医学・健康",
    description="身体部位、常见疾病、医院就诊、健康生活等相关词汇的网络",
    center_words=["病院", "健康", "体"],
    words=[
        VocabWord(word="病院", reading="びょういん", meaning="医院", level="N5", pos="名詞",
                  example_jp="病院へ行く。", example_zh="去医院。",
                  example_reading="びょういんへいく", related=["医者", "薬"]),
        VocabWord(word="医者", reading="いしゃ", meaning="医生", level="N5", pos="名詞",
                  example_jp="医者に診てもらう。", example_zh="让医生看病。",
                  example_reading="いしゃにみてもらう", related=["病院", "看護師"]),
        VocabWord(word="薬", reading="くすり", meaning="药", level="N5", pos="名詞",
                  example_jp="薬を飲む。", example_zh="吃药。",
                  example_reading="くすりをのむ", related=["病院", "痛み"]),
        VocabWord(word="体", reading="からだ", meaning="身体", level="N5", pos="名詞",
                  example_jp="体の調子が悪い。", example_zh="身体不舒服。",
                  example_reading="からだのちょうしがわるい", related=["健康", "病気"]),
        VocabWord(word="健康", reading="けんこう", meaning="健康", level="N4", pos="名詞",
                  example_jp="健康に気をつける。", example_zh="注意健康。",
                  example_reading="けんこうにきをつける", related=["体", "運動"]),
        VocabWord(word="病気", reading="びょうき", meaning="疾病", level="N4", pos="名詞",
                  example_jp="病気で学校を休む。", example_zh="因病请假不上学。",
                  example_reading="びょうきでがっこうをやすむ", related=["病院", "症状"]),
        VocabWord(word="症状", reading="しょうじょう", meaning="症状", level="N2", pos="名詞",
                  example_jp="症状を説明する。", example_zh="说明症状。",
                  example_reading="しょうじょうをせつめいする", related=["病気", "熱"]),
        VocabWord(word="熱", reading="ねつ", meaning="发烧/热度", level="N4", pos="名詞",
                  example_jp="熱がある。", example_zh="发烧了。",
                  example_reading="ねつがある", related=["病気", "風邪"]),
        VocabWord(word="風邪", reading="かぜ", meaning="感冒", level="N4", pos="名詞",
                  example_jp="風邪をひいた。", example_zh="感冒了。",
                  example_reading="かぜをひいた", related=["熱", "咳"]),
        VocabWord(word="咳", reading="せき", meaning="咳嗽", level="N3", pos="名詞",
                  example_jp="咳が止まらない。", example_zh="咳嗽不停。",
                  example_reading="せきがとまらない", related=["風邪", "のど"]),
        VocabWord(word="頭", reading="あたま", meaning="头", level="N5", pos="名詞",
                  example_jp="頭が痛い。", example_zh="头疼。",
                  example_reading="あたまがいたい", related=["体", "痛み"]),
        VocabWord(word="痛み", reading="いたみ", meaning="疼痛", level="N3", pos="名詞",
                  example_jp="痛みを感じる。", example_zh="感到疼痛。",
                  example_reading="いたみをかんじる", related=["頭", "薬"]),
        VocabWord(word="手術", reading="しゅじゅつ", meaning="手术", level="N2", pos="名詞",
                  example_jp="手術を受ける。", example_zh="接受手术。",
                  example_reading="しゅじゅつをうける", related=["病院", "医者"]),
        VocabWord(word="検査", reading="けんさ", meaning="检查/体检", level="N3", pos="名詞",
                  example_jp="血液検査をする。", example_zh="做血液检查。",
                  example_reading="けつえきけんさをする", related=["病院", "結果"]),
        VocabWord(word="注射", reading="ちゅうしゃ", meaning="注射/打针", level="N3", pos="名詞",
                  example_jp="注射を打つ。", example_zh="打针。",
                  example_reading="ちゅうしゃをうつ", related=["病院", "痛み"]),
        VocabWord(word="看護師", reading="かんごし", meaning="护士", level="N3", pos="名詞",
                  example_jp="看護師に相談する。", example_zh="向护士咨询。",
                  example_reading="かんごしにそうだんする", related=["医者", "病院"]),
        VocabWord(word="薬局", reading="やっきょく", meaning="药房", level="N3", pos="名詞",
                  example_jp="薬局で薬を買う。", example_zh="在药房买药。",
                  example_reading="やっきょくでくすりをかう", related=["薬", "病院"]),
        VocabWord(word="救急車", reading="きゅうきゅうしゃ", meaning="救护车", level="N3", pos="名詞",
                  example_jp="救急車を呼ぶ。", example_zh="叫救护车。",
                  example_reading="きゅうきゅうしゃをよぶ", related=["病院", "緊急"]),
        VocabWord(word="治療", reading="ちりょう", meaning="治疗", level="N2", pos="名詞",
                  example_jp="治療を受ける。", example_zh="接受治疗。",
                  example_reading="ちりょうをうける", related=["病院", "手術"]),
        VocabWord(word="予約", reading="よやく", meaning="预约", level="N3", pos="名詞/サ変",
                  example_jp="病院の予約を取る。", example_zh="预约医院。",
                  example_reading="びょういんのよやくをとる", related=["病院", "診察"]),
    ],
    grammar_points=[
        {"pattern": "〜が痛（いた）い", "meaning": "…疼/痛", "example": "頭が痛い。", "level": "N5"},
        {"pattern": "〜を休（やす）む", "meaning": "请假…", "example": "病気で学校を休む。", "level": "N4"},
        {"pattern": "〜に気（き）をつける", "meaning": "注意…", "example": "健康に気をつける。", "level": "N4"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 交通・移動 / Transportation
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="transport",
    domain_name="交通与出行",
    domain_name_ja="交通・移動",
    description="交通工具、出行方式、道路、车站等相关词汇的网络",
    center_words=["電車", "車", "駅"],
    words=[
        VocabWord(word="駅", reading="えき", meaning="车站", level="N4", pos="名詞",
                  example_jp="駅で切符を買う。", example_zh="在车站买票。",
                  example_reading="えきできっぷをかう", related=["電車", "改札"]),
        VocabWord(word="電車", reading="でんしゃ", meaning="电车/火车", level="N4", pos="名詞",
                  example_jp="電車に乗る。", example_zh="坐电车。",
                  example_reading="でんしゃにのる", related=["駅", "切符"]),
        VocabWord(word="切符", reading="きっぷ", meaning="票", level="N4", pos="名詞",
                  example_jp="切符を買う。", example_zh="买票。",
                  example_reading="きっぷをかう", related=["駅", "電車"]),
        VocabWord(word="バス", reading="ばす", meaning="公交车", level="N4", pos="名詞",
                  example_jp="バスで学校に行く。", example_zh="坐公交去学校。",
                  example_reading="ばすでがっこうにいく", related=["停留所", "運転手"]),
        VocabWord(word="車", reading="くるま", meaning="汽车", level="N5", pos="名詞",
                  example_jp="車を運転する。", example_zh="开车。",
                  example_reading="くるまをうんてんする", related=["運転", "駐車場"]),
        VocabWord(word="運転", reading="うんてん", meaning="驾驶", level="N3", pos="名詞/サ変",
                  example_jp="安全運転に気をつける。", example_zh="注意安全驾驶。",
                  example_reading="あんぜんうんてんにきをつける", related=["車", "免許"]),
        VocabWord(word="免許", reading="めんきょ", meaning="执照/驾照", level="N3", pos="名詞",
                  example_jp="運転免許を取る。", example_zh="考取驾照。",
                  example_reading="うんてんめんきょをとる", related=["運転", "試験"]),
        VocabWord(word="自転車", reading="じてんしゃ", meaning="自行车", level="N4", pos="名詞",
                  example_jp="自転車で買い物に行く。", example_zh="骑自行车去购物。",
                  example_reading="じてんしゃでかいものにいく", related=["乗る", "道"]),
        VocabWord(word="飛行機", reading="ひこうき", meaning="飞机", level="N4", pos="名詞",
                  example_jp="飛行機で東京へ行く。", example_zh="坐飞机去东京。",
                  example_reading="ひこうきでとうきょうへいく", related=["空港", "旅"]),
        VocabWord(word="空港", reading="くうこう", meaning="机场", level="N3", pos="名詞",
                  example_jp="空港に着いた。", example_zh="到达机场。",
                  example_reading="くうこうについた", related=["飛行機", "旅券"]),
        VocabWord(word="旅券", reading="りょけん", meaning="护照", level="N2", pos="名詞",
                  example_jp="旅券を見せる。", example_zh="出示护照。",
                  example_reading="りょけんをみせる", related=["空港", "海外"]),
        VocabWord(word="道", reading="みち", meaning="道路", level="N5", pos="名詞",
                  example_jp="道を渡る。", example_zh="过马路。",
                  example_reading="みちをわたる", related=["信号", "交差点"]),
        VocabWord(word="信号", reading="しんごう", meaning="交通信号", level="N4", pos="名詞",
                  example_jp="信号が青になった。", example_zh="信号变绿了。",
                  example_reading="しんごうがあおになった", related=["道", "交差点"]),
        VocabWord(word="交差点", reading="こうさてん", meaning="十字路口", level="N3", pos="名詞",
                  example_jp="交差点を右に曲がる。", example_zh="在十字路口右转。",
                  example_reading="こうさてんをみぎにまがる", related=["信号", "道"]),
        VocabWord(word="駐車場", reading="ちゅうしゃじょう", meaning="停车场", level="N3", pos="名詞",
                  example_jp="駐車場に車を止める。", example_zh="把车停在停车场。",
                  example_reading="ちゅうしゃじょうにくるまをとめる", related=["車", "運転"]),
        VocabWord(word="地図", reading="ちず", meaning="地图", level="N4", pos="名詞",
                  example_jp="地図で道を調べる。", example_zh="用地图查路。",
                  example_reading="ちずでみちをしらべる", related=["道", "案内"]),
        VocabWord(word="乗り換え", reading="のりかえ", meaning="换乘", level="N3", pos="名詞",
                  example_jp="次の駅で乗り換える。", example_zh="在下一站换乘。",
                  example_reading="つぎのえきでのりかえる", related=["電車", "駅"]),
        VocabWord(word="改札", reading="かいさつ", meaning="检票口", level="N3", pos="名詞",
                  example_jp="改札を通る。", example_zh="通过检票口。",
                  example_reading="かいさつをとおる", related=["駅", "切符"]),
        VocabWord(word="急行", reading="きゅうこう", meaning="快车", level="N3", pos="名詞",
                  example_jp="急行に乗る。", example_zh="坐快车。",
                  example_reading="きゅうこうにのる", related=["電車", "特急"]),
        VocabWord(word="渋滞", reading="じゅうたい", meaning="堵车", level="N2", pos="名詞",
                  example_jp="道が渋滞している。", example_zh="路上堵车了。",
                  example_reading="みちがじゅうたいしている", related=["車", "道"]),
    ],
    grammar_points=[
        {"pattern": "〜に乗（の）る", "meaning": "乘坐…", "example": "電車に乗る。", "level": "N5"},
        {"pattern": "〜で行（い）く", "meaning": "用…去（交通工具）", "example": "バスで学校に行く。", "level": "N5"},
        {"pattern": "〜に着（つ）く", "meaning": "到达…", "example": "空港に着いた。", "level": "N4"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 商务・事務 / Business & Office
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="business",
    domain_name="商务与办公",
    domain_name_ja="ビジネス・事務",
    description="商务沟通、办公室事务、会议、金融等相关词汇的网络",
    center_words=["会社", "仕事", "会議"],
    words=[
        VocabWord(word="会社", reading="かいしゃ", meaning="公司", level="N4", pos="名詞",
                  example_jp="会社で働く。", example_zh="在公司工作。",
                  example_reading="かいしゃではたらく", related=["仕事", "社長"]),
        VocabWord(word="仕事", reading="しごと", meaning="工作", level="N5", pos="名詞",
                  example_jp="仕事を探す。", example_zh="找工作。",
                  example_reading="しごとをさがす", related=["会社", "面接"]),
        VocabWord(word="会議", reading="かいぎ", meaning="会议", level="N3", pos="名詞",
                  example_jp="会議に出席する。", example_zh="出席会议。",
                  example_reading="かいぎにしゅっせきする", related=["資料", "発表"]),
        VocabWord(word="資料", reading="しりょう", meaning="资料", level="N3", pos="名詞",
                  example_jp="会議の資料を準備する。", example_zh="准备会议资料。",
                  example_reading="かいぎのしりょうをじゅんびする", related=["会議", "書類"]),
        VocabWord(word="書類", reading="しょるい", meaning="文件/文书", level="N3", pos="名詞",
                  example_jp="書類に印鑑を押す。", example_zh="在文件上盖章。",
                  example_reading="しょるいにいんかんをおす", related=["資料", "契約"]),
        VocabWord(word="契約", reading="けいやく", meaning="合同", level="N2", pos="名詞",
                  example_jp="契約を結ぶ。", example_zh="签订合同。",
                  example_reading="けいやくをむすぶ", related=["書類", "取引"]),
        VocabWord(word="社長", reading="しゃちょう", meaning="社长/总经理", level="N3", pos="名詞",
                  example_jp="社長に報告する。", example_zh="向社长汇报。",
                  example_reading="しゃちょうにほうこくする", related=["会社", "上司"]),
        VocabWord(word="上司", reading="じょうし", meaning="上司", level="N3", pos="名詞",
                  example_jp="上司に相談する。", example_zh="和上司商量。",
                  example_reading="じょうしにそうだんする", related=["社長", "同僚"]),
        VocabWord(word="同僚", reading="どうりょう", meaning="同事", level="N2", pos="名詞",
                  example_jp="同僚と協力する。", example_zh="和同事合作。",
                  example_reading="どうりょうときょうりょくする", related=["上司", "仕事"]),
        VocabWord(word="報告", reading="ほうこく", meaning="报告/汇报", level="N3", pos="名詞/サ変",
                  example_jp="結果を報告する。", example_zh="汇报结果。",
                  example_reading="けっかをほうこくする", related=["会議", "連絡"]),
        VocabWord(word="連絡", reading="れんらく", meaning="联系", level="N3", pos="名詞/サ変",
                  example_jp="メールで連絡する。", example_zh="用邮件联系。",
                  example_reading="めーるでれんらくする", related=["報告", "相談"]),
        VocabWord(word="相談", reading="そうだん", meaning="商量/咨询", level="N3", pos="名詞/サ変",
                  example_jp="問題を相談する。", example_zh="商量问题。",
                  example_reading="もんだいをそうだんする", related=["連絡", "上司"]),
        VocabWord(word="取引", reading="とりひき", meaning="交易", level="N2", pos="名詞",
                  example_jp="新しい取引を始める。", example_zh="开始新的交易。",
                  example_reading="あたらしいとりひきをはじめる", related=["契約", "会社"]),
        VocabWord(word="銀行", reading="ぎんこう", meaning="银行", level="N4", pos="名詞",
                  example_jp="銀行でお金を引き出す。", example_zh="在银行取钱。",
                  example_reading="ぎんこうでおかねをひきだす", related=["口座", "貯金"]),
        VocabWord(word="口座", reading="こうざ", meaning="账户", level="N3", pos="名詞",
                  example_jp="銀行口座を開く。", example_zh="开银行账户。",
                  example_reading="ぎんこうこうざをひらく", related=["銀行", "貯金"]),
        VocabWord(word="貯金", reading="ちょきん", meaning="储蓄", level="N3", pos="名詞/サ変",
                  example_jp="毎月貯金する。", example_zh="每月储蓄。",
                  example_reading="まいつきちょきんする", related=["銀行", "口座"]),
        VocabWord(word="出張", reading="しゅっちょう", meaning="出差", level="N3", pos="名詞",
                  example_jp="来週大阪へ出張する。", example_zh="下周去大阪出差。",
                  example_reading="らいしゅうおおさかへしゅっちょうする", related=["仕事", "旅"]),
        VocabWord(word="給料", reading="きゅうりょう", meaning="工资", level="N3", pos="名詞",
                  example_jp="給料が上がった。", example_zh="涨工资了。",
                  example_reading="きゅうりょうがあがった", related=["仕事", "銀行"]),
        VocabWord(word="名刺", reading="めいし", meaning="名片", level="N3", pos="名詞",
                  example_jp="名刺を交換する。", example_zh="交换名片。",
                  example_reading="めいしをこうかんする", related=["会社", "仕事"]),
        VocabWord(word="企画", reading="きかく", meaning="规划/策划", level="N2", pos="名詞",
                  example_jp="新しい企画を提案する。", example_zh="提出新的企划案。",
                  example_reading="あたらしいきかくをていあんする", related=["会議", "提案"]),
    ],
    grammar_points=[
        {"pattern": "〜に出席（しゅっせき）する", "meaning": "出席…", "example": "会議に出席する。", "level": "N3"},
        {"pattern": "〜を報告（ほうこく）する", "meaning": "汇报…", "example": "結果を報告する。", "level": "N3"},
        {"pattern": "〜に相談（そうだん）する", "meaning": "和…商量", "example": "上司に相談する。", "level": "N3"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 運動・スポーツ / Sports
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="sports",
    domain_name="体育运动",
    domain_name_ja="スポーツ・運動",
    description="体育运动、比赛、锻炼、健身等相关词汇的网络",
    center_words=["スポーツ", "運動", "試合"],
    words=[
        VocabWord(word="運動", reading="うんどう", meaning="运动", level="N4", pos="名詞",
                  example_jp="毎日運動する。", example_zh="每天运动。",
                  example_reading="まいにちうんどうする", related=["スポーツ", "健康"]),
        VocabWord(word="試合", reading="しあい", meaning="比赛", level="N3", pos="名詞",
                  example_jp="サッカーの試合を見る。", example_zh="看足球比赛。",
                  example_reading="さっかーのしあいをみる", related=["勝つ", "負ける"]),
        VocabWord(word="勝つ", reading="かつ", meaning="赢", level="N4", pos="動詞",
                  example_jp="試合に勝った。", example_zh="赢了比赛。",
                  example_reading="しあいにかった", related=["試合", "負ける"]),
        VocabWord(word="負ける", reading="まける", meaning="输", level="N4", pos="動詞",
                  example_jp="0対3で負けた。", example_zh="以0比3输了。",
                  example_reading="れいたいさんでまけた", related=["試合", "勝つ"]),
        VocabWord(word="選手", reading="せんしゅ", meaning="选手", level="N3", pos="名詞",
                  example_jp="日本の選手を応援する。", example_zh="为日本选手加油。",
                  example_reading="にほんのせんしゅをおうえんする", related=["試合", "チーム"]),
        VocabWord(word="チーム", reading="ちーむ", meaning="团队", level="N3", pos="名詞",
                  example_jp="チームで練習する。", example_zh="团队练习。",
                  example_reading="ちーむでれんしゅうする", related=["選手", "試合"]),
        VocabWord(word="練習", reading="れんしゅう", meaning="练习", level="N3", pos="名詞/サ変",
                  example_jp="毎日ピアノを練習する。", example_zh="每天练习钢琴。",
                  example_reading="まいにちぴあのをれんしゅうする", related=["運動", "上達"]),
        VocabWord(word="走る", reading="はしる", meaning="跑步", level="N5", pos="動詞",
                  example_jp="公園を走る。", example_zh="在公园跑步。",
                  example_reading="こうえんをはしる", related=["運動", "マラソン"]),
        VocabWord(word="泳ぐ", reading="およぐ", meaning="游泳", level="N5", pos="動詞",
                  example_jp="プールで泳ぐ。", example_zh="在泳池游泳。",
                  example_reading="ぷーるでおよぐ", related=["運動", "海"]),
        VocabWord(word="サッカー", reading="さっかー", meaning="足球", level="N4", pos="名詞",
                  example_jp="サッカーが好きだ。", example_zh="喜欢足球。",
                  example_reading="さっかーがすきだ", related=["試合", "チーム"]),
        VocabWord(word="野球", reading="やきゅう", meaning="棒球", level="N4", pos="名詞",
                  example_jp="野球の試合を見に行く。", example_zh="去看棒球比赛。",
                  example_reading="やきゅうのしあいをみにいく", related=["試合", "選手"]),
        VocabWord(word="テニス", reading="てにす", meaning="网球", level="N4", pos="名詞",
                  example_jp="テニスコートを予約する。", example_zh="预约网球场。",
                  example_reading="てにすこーとをよやくする", related=["運動", "練習"]),
        VocabWord(word="体育館", reading="たいいくかん", meaning="体育馆", level="N3", pos="名詞",
                  example_jp="体育館でバスケをする。", example_zh="在体育馆打篮球。",
                  example_reading="たいいくかんでばすけをする", related=["運動", "練習"]),
        VocabWord(word="応援", reading="おうえん", meaning="加油/助威", level="N3", pos="名詞/サ変",
                  example_jp="チームを応援する。", example_zh="为团队加油。",
                  example_reading="ちーむをおうえんする", related=["試合", "選手"]),
        VocabWord(word="優勝", reading="ゆうしょう", meaning="冠军/获胜", level="N2", pos="名詞",
                  example_jp="大会で優勝した。", example_zh="在大会上夺冠。",
                  example_reading="たいかいでゆうしょうした", related=["試合", "勝つ"]),
        VocabWord(word="金", reading="きん", meaning="金牌/金", level="N4", pos="名詞",
                  example_jp="金メダルを取った。", example_zh="获得了金牌。",
                  example_reading="きんめだるをとった", related=["優勝", "試合"]),
        VocabWord(word="体力", reading="たいりょく", meaning="体力", level="N3", pos="名詞",
                  example_jp="体力をつける。", example_zh="增强体力。",
                  example_reading="たいりょくをつける", related=["運動", "健康"]),
        VocabWord(word="汗", reading="あせ", meaning="汗水", level="N3", pos="名詞",
                  example_jp="汗をかく。", example_zh="出汗。",
                  example_reading="あせをかく", related=["運動", "走る"]),
        VocabWord(word="筋肉", reading="きんにく", meaning="肌肉", level="N2", pos="名詞",
                  example_jp="筋肉を鍛える。", example_zh="锻炼肌肉。",
                  example_reading="きんにくをきたえる", related=["運動", "体力"]),
        VocabWord(word="怪我", reading="けが", meaning="受伤", level="N4", pos="名詞",
                  example_jp="運動で怪我をした。", example_zh="运动时受伤了。",
                  example_reading="うんどうでけがをした", related=["病院", "痛み"]),
    ],
    grammar_points=[
        {"pattern": "〜に勝（か）つ", "meaning": "战胜…", "example": "試合に勝った。", "level": "N4"},
        {"pattern": "〜を応援（おうえん）する", "meaning": "为…加油", "example": "チームを応援する。", "level": "N3"},
        {"pattern": "〜で優勝（ゆうしょう）する", "meaning": "在…夺冠", "example": "大会で優勝した。", "level": "N2"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 教育・学校 / Education & School
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="education",
    domain_name="教育与学校",
    domain_name_ja="教育・学校",
    description="学校教育、课程、考试、学习活动等相关词汇的网络",
    center_words=["学校", "勉強", "先生"],
    words=[
        VocabWord(word="学校", reading="がっこう", meaning="学校", level="N5", pos="名詞",
                  example_jp="学校に行く。", example_zh="去学校。",
                  example_reading="がっこうにいく", related=["勉強", "先生"]),
        VocabWord(word="勉強", reading="べんきょう", meaning="学习", level="N5", pos="名詞/サ変",
                  example_jp="日本語を勉強する。", example_zh="学习日语。",
                  example_reading="にほんごをべんきょうする", related=["学校", "宿題"]),
        VocabWord(word="先生", reading="せんせい", meaning="老师", level="N5", pos="名詞",
                  example_jp="先生に質問する。", example_zh="向老师提问。",
                  example_reading="せんせいにしつもんする", related=["学校", "授業"]),
        VocabWord(word="授業", reading="じゅぎょう", meaning="课程/上课", level="N4", pos="名詞",
                  example_jp="授業を受ける。", example_zh="上课。",
                  example_reading="じゅぎょうをうける", related=["先生", "学生"]),
        VocabWord(word="学生", reading="がくせい", meaning="学生", level="N5", pos="名詞",
                  example_jp="学生は図書館で勉強する。", example_zh="学生在图书馆学习。",
                  example_reading="がくせいはとしょかんでべんきょうする", related=["学校", "先生"]),
        VocabWord(word="宿題", reading="しゅくだい", meaning="作业", level="N4", pos="名詞",
                  example_jp="宿題をする。", example_zh="做作业。",
                  example_reading="しゅくだいをする", related=["勉強", "学校"]),
        VocabWord(word="試験", reading="しけん", meaning="考试", level="N4", pos="名詞",
                  example_jp="試験に合格する。", example_zh="通过考试。",
                  example_reading="しけんにごうかくする", related=["勉強", "合格"]),
        VocabWord(word="合格", reading="ごうかく", meaning="合格/通过", level="N3", pos="名詞/サ変",
                  example_jp="試験に合格した。", example_zh="通过了考试。",
                  example_reading="しけんにごうかくした", related=["試験", "勉強"]),
        VocabWord(word="大学", reading="だいがく", meaning="大学", level="N4", pos="名詞",
                  example_jp="大学に入る。", example_zh="上大学。",
                  example_reading="だいがくにはいる", related=["学校", "学生"]),
        VocabWord(word="入学", reading="にゅうがく", meaning="入学", level="N3", pos="名詞",
                  example_jp="入学式に参加する。", example_zh="参加开学典礼。",
                  example_reading="にゅうがくしきにさんかする", related=["大学", "卒業"]),
        VocabWord(word="卒業", reading="そつぎょう", meaning="毕业", level="N3", pos="名詞",
                  example_jp="大学を卒業する。", example_zh="从大学毕业。",
                  example_reading="だいがくをそつぎょうする", related=["入学", "学校"]),
        VocabWord(word="教科書", reading="きょうかしょ", meaning="教科书", level="N3", pos="名詞",
                  example_jp="教科書を開く。", example_zh="打开教科书。",
                  example_reading="きょうかしょをひらく", related=["勉強", "授業"]),
        VocabWord(word="図書館", reading="としょかん", meaning="图书馆", level="N4", pos="名詞",
                  example_jp="図書館で本を借りる。", example_zh="在图书馆借书。",
                  example_reading="としょかんでほんをかりる", related=["本", "勉強"]),
        VocabWord(word="辞書", reading="じしょ", meaning="词典", level="N4", pos="名詞",
                  example_jp="辞書で単語を調べる。", example_zh="用词典查单词。",
                  example_reading="じしょでたんごをしらべる", related=["勉強", "言葉"]),
        VocabWord(word="質問", reading="しつもん", meaning="提问", level="N4", pos="名詞/サ変",
                  example_jp="質問してもいいですか。", example_zh="可以提问吗？",
                  example_reading="しつもんしてもいいですか", related=["先生", "答える"]),
        VocabWord(word="答える", reading="こたえる", meaning="回答", level="N4", pos="動詞",
                  example_jp="質問に答える。", example_zh="回答问题。",
                  example_reading="しつもんにこたえる", related=["質問", "先生"]),
        VocabWord(word="成績", reading="せいせき", meaning="成绩", level="N3", pos="名詞",
                  example_jp="成績が上がった。", example_zh="成绩提高了。",
                  example_reading="せいせきがあがった", related=["試験", "合格"]),
        VocabWord(word="留学", reading="りゅうがく", meaning="留学", level="N3", pos="名詞",
                  example_jp="日本に留学する。", example_zh="去日本留学。",
                  example_reading="にほんにりゅうがくする", related=["大学", "外国"]),
        VocabWord(word="教育", reading="きょういく", meaning="教育", level="N3", pos="名詞",
                  example_jp="教育は大切だ。", example_zh="教育很重要。",
                  example_reading="きょういくはたいせつだ", related=["学校", "先生"]),
        VocabWord(word="学ぶ", reading="まなぶ", meaning="学习/学会", level="N3", pos="動詞",
                  example_jp="新しい技術を学ぶ。", example_zh="学习新技术。",
                  example_reading="あたらしいぎじゅつをまなぶ", related=["勉強", "教育"]),
    ],
    grammar_points=[
        {"pattern": "〜に質問（しつもん）する", "meaning": "向…提问", "example": "先生に質問する。", "level": "N4"},
        {"pattern": "〜に合格（ごうかく）する", "meaning": "通过…（考试）", "example": "試験に合格する。", "level": "N3"},
        {"pattern": "〜を卒業（そつぎょう）する", "meaning": "从…毕业", "example": "大学を卒業する。", "level": "N3"},
    ],
))

# ═══════════════════════════════════════════════════════════════
# 買い物・ショッピング / Shopping
# ═══════════════════════════════════════════════════════════════

_register(VocabNetwork(
    domain_id="shopping",
    domain_name="购物消费",
    domain_name_ja="買い物・ショッピング",
    description="购物、价格、支付、商店类型、消费等相关词汇的网络",
    center_words=["買い物", "店", "お金"],
    words=[
        VocabWord(word="買い物", reading="かいもの", meaning="购物", level="N5", pos="名詞/サ変",
                  example_jp="買い物に行く。", example_zh="去购物。",
                  example_reading="かいものにいく", related=["店", "買う"]),
        VocabWord(word="店", reading="みせ", meaning="商店", level="N5", pos="名詞",
                  example_jp="この店は安い。", example_zh="这家店很便宜。",
                  example_reading="このみせはやすい", related=["買い物", "商品"]),
        VocabWord(word="買う", reading="かう", meaning="买", level="N5", pos="動詞",
                  example_jp="新しい服を買う。", example_zh="买新衣服。",
                  example_reading="あたらしいふくをかう", related=["買い物", "売る"]),
        VocabWord(word="売る", reading="うる", meaning="卖", level="N4", pos="動詞",
                  example_jp="店で野菜を売る。", example_zh="在店里卖蔬菜。",
                  example_reading="みせでやさいをうる", related=["買う", "商品"]),
        VocabWord(word="お金", reading="おかね", meaning="钱", level="N5", pos="名詞",
                  example_jp="お金を払う。", example_zh="付钱。",
                  example_reading="おかねをはらう", related=["買う", "値段"]),
        VocabWord(word="値段", reading="ねだん", meaning="价格", level="N4", pos="名詞",
                  example_jp="値段を確認する。", example_zh="确认价格。",
                  example_reading="ねだんをかくにんする", related=["お金", "安い"]),
        VocabWord(word="安い", reading="やすい", meaning="便宜", level="N5", pos="形容詞",
                  example_jp="この店の商品は安い。", example_zh="这家店的东西便宜。",
                  example_reading="このみせのしょうひんはやすい", related=["値段", "高い"]),
        VocabWord(word="高い", reading="たかい", meaning="贵/高", level="N5", pos="形容詞",
                  example_jp="このかばんは高い。", example_zh="这个包很贵。",
                  example_reading="このかばんはたかい", related=["値段", "安い"]),
        VocabWord(word="商品", reading="しょうひん", meaning="商品", level="N3", pos="名詞",
                  example_jp="商品を比べる。", example_zh="比较商品。",
                  example_reading="しょうひんをくらべる", related=["店", "買い物"]),
        VocabWord(word="スーパー", reading="すーぱー", meaning="超市", level="N4", pos="名詞",
                  example_jp="スーパーで食材を買う。", example_zh="在超市买食材。",
                  example_reading="すーぱーでしょくざいをかう", related=["店", "買い物"]),
        VocabWord(word="デパート", reading="でぱーと", meaning="百货商场", level="N4", pos="名詞",
                  example_jp="デパートの地下でお菓子を買う。", example_zh="在百货商场地下买点心。",
                  example_reading="でぱーとのちかでおかしをかう", related=["店", "買い物"]),
        VocabWord(word="コンビニ", reading="こんびに", meaning="便利店", level="N4", pos="名詞",
                  example_jp="コンビニで弁当を買う。", example_zh="在便利店买便当。",
                  example_reading="こんびにでべんとうをかう", related=["店", "スーパー"]),
        VocabWord(word="割引", reading="わりびき", meaning="折扣", level="N3", pos="名詞",
                  example_jp="割引クーポンを使う。", example_zh="使用折扣券。",
                  example_reading="わりびきくーぽんをつかう", related=["値段", "安い"]),
        VocabWord(word="レジ", reading="れじ", meaning="收银台", level="N4", pos="名詞",
                  example_jp="レジでお金を払う。", example_zh="在收银台付钱。",
                  example_reading="れじでおかねをはらう", related=["お金", "店"]),
        VocabWord(word="領収書", reading="りょうしゅうしょ", meaning="收据", level="N3", pos="名詞",
                  example_jp="領収書をもらう。", example_zh="拿收据。",
                  example_reading="りょうしゅうしょをもらう", related=["レジ", "お金"]),
        VocabWord(word="袋", reading="ふくろ", meaning="袋子", level="N4", pos="名詞",
                  example_jp="袋をください。", example_zh="请给我袋子。",
                  example_reading="ふくろをください", related=["買い物", "商品"]),
        VocabWord(word="現金", reading="げんきん", meaning="现金", level="N3", pos="名詞",
                  example_jp="現金で払う。", example_zh="用现金支付。",
                  example_reading="げんきんではらう", related=["お金", "カード"]),
        VocabWord(word="返品", reading="へんぴん", meaning="退货", level="N3", pos="名詞",
                  example_jp="商品を返品する。", example_zh="退货。",
                  example_reading="しょうひんをへんぴんする", related=["買い物", "交換"]),
        VocabWord(word="交換", reading="こうかん", meaning="交换/换货", level="N3", pos="名詞/サ変",
                  example_jp="サイズを交換する。", example_zh="换尺码。",
                  example_reading="さいずをこうかんする", related=["返品", "商品"]),
        VocabWord(word="税", reading="ぜい", meaning="税", level="N3", pos="名詞",
                  example_jp="消費税が上がった。", example_zh="消费税涨了。",
                  example_reading="しょうひぜいがあがった", related=["お金", "値段"]),
    ],
    grammar_points=[
        {"pattern": "〜で払（はら）う", "meaning": "用…支付", "example": "現金で払う。", "level": "N4"},
        {"pattern": "〜をください", "meaning": "请给我…", "example": "袋をください。", "level": "N5"},
        {"pattern": "〜を交換（こうかん）する", "meaning": "更换…", "example": "サイズを交換する。", "level": "N3"},
    ],
))


def get_all_domains(language: str = "") -> List[Dict]:
    """Get list of all available vocabulary domains, optionally filtered by language."""
    networks = [v for v in VOCAB_NETWORKS.values() if not language or v.language == language]
    return [
        {
            "domain_id": v.domain_id,
            "domain_name": v.domain_name,
            "domain_name_ja": v.domain_name_ja,
            "description": v.description,
            "word_count": len(v.words),
            "center_words": v.center_words,
            "levels": sorted(set(w.level for w in v.words)),
            "language": v.language,
        }
        for v in networks
    ]


def get_networks_by_language(language: str) -> List[VocabNetwork]:
    """Return all VocabNetwork objects for a study language."""
    return [v for v in VOCAB_NETWORKS.values() if v.language == language]


def get_domain(domain_id: str) -> Optional[VocabNetwork]:
    """Get a specific vocabulary domain."""
    return VOCAB_NETWORKS.get(domain_id)


def get_domain_words(domain_id: str, level: str = "") -> List[VocabWord]:
    """Get words from a domain, optionally filtered by JLPT level."""
    network = VOCAB_NETWORKS.get(domain_id)
    if not network:
        return []
    if level:
        return [w for w in network.words if w.level == level]
    return network.words


def get_related_words(word: str, domain_id: str = "") -> List[VocabWord]:
    """Find words related to a given word across all domains."""
    results = []
    search_domains = [VOCAB_NETWORKS[domain_id]] if domain_id else list(VOCAB_NETWORKS.values())

    for network in search_domains:
        for w in network.words:
            if w.word == word or w.reading == word or w.meaning == word:
                for rel_id in w.related:
                    for w2 in network.words:
                        if w2.word == rel_id:
                            results.append(w2)
                break

    return results


def search_vocabulary(query: str, domain_id: str = "", level: str = "") -> List[Dict]:
    """Search vocabulary across all domains by word, reading, or meaning."""
    results = []
    search_domains = [VOCAB_NETWORKS[domain_id]] if domain_id and domain_id in VOCAB_NETWORKS else list(VOCAB_NETWORKS.values())

    query_lower = query.lower()

    for network in search_domains:
        for w in network.words:
            if level and w.level != level:
                continue
            if (query_lower in w.word.lower() or
                query_lower in w.reading.lower() or
                query_lower in w.meaning.lower() or
                any(query_lower in tag.lower() for tag in w.tags)):
                results.append({
                    **w.to_dict(),
                    "domain_id": network.domain_id,
                    "domain_name": network.domain_name,
                    "domain_name_ja": network.domain_name_ja,
                })

    return results