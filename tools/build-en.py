#!/usr/bin/env python3
"""
영문판(/en) 생성기.

한국어 원본 HTML의 구조를 그대로 두고 문구만 영문으로 바꿉니다.
한국어 쪽을 고친 뒤 이 스크립트를 다시 돌리면 영문판이 갱신됩니다.

    python3 tools/build-en.py

모든 치환은 원본에 정확히 1회 존재해야 하며, 하나라도 어긋나면 즉시 멈춥니다.
생성 후 한글이 남아 있으면 오류로 처리합니다.
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "space.html", "healing.html", "info.html"]
SITE = "https://gangsanjae.vercel.app"

# 문의 창구 — 이메일 확보 시 EMAIL 만 채우면 전 페이지에 반영됩니다.
EMAIL = None
INSTAGRAM = "https://www.instagram.com/hanokhotel_kangsanjae/"
TEL_HREF = "tel:+821090277662"
TEL_TEXT = "+82 10-9027-7662"

def enquiry_href():
    return f"mailto:{EMAIL}" if EMAIL else INSTAGRAM

def enquiry_label():
    return "Email us" if EMAIL else "Message us on Instagram"

# ---------------------------------------------------------------- 공통 문구
COMMON = [
    # 헤더 · 내비게이션
    ('<a href="/" class="logo">강산재</a>', '<a href="/en" class="logo">Gangsanjae</a>'),
    ('<a href="/#story">강산재 이야기</a>', '<a href="/en#story">Our Story</a>'),
    ('<a href="/space">공간</a>', '<a href="/en/space">The Space</a>'),
    ('<a href="/space" class="on">공간</a>', '<a href="/en/space" class="on">The Space</a>', True),
    ('<a href="/healing">치유 프로그램</a>', '<a href="/en/healing">Healing</a>'),
    ('<a href="/healing" class="on">치유 프로그램</a>', '<a href="/en/healing" class="on">Healing</a>', True),
    ('<a href="/info">이용안내</a>', '<a href="/en/info">Information</a>'),
    ('<a href="/info" class="on">이용안내</a>', '<a href="/en/info" class="on">Information</a>', True),
    ('<a href="/info#location">오시는 길</a>', '<a href="/en/info#location">Getting Here</a>'),
    ('<a href="#location">오시는 길</a>', '<a href="#location">Getting Here</a>'),
    ('<a href="/#review">후기</a>', '<a href="/en#review">Reviews</a>'),
    ('<label for="nav" class="nav-btn" tabindex="0" aria-label="메뉴 열기">',
     '<label for="nav" class="nav-btn" tabindex="0" aria-label="Open menu">'),
    ('<a href="#booking" class="btn btn-primary btn-sm">예약 문의</a>',
     '<a href="#booking" class="btn btn-primary btn-sm">Enquire</a>'),
    ('<a href="/#booking" class="btn btn-primary btn-sm">예약 문의</a>',
     '<a href="/en#booking" class="btn btn-primary btn-sm">Enquire</a>'),
    ('<a href="#contact" class="btn btn-primary btn-sm">예약 문의</a>',
     '<a href="#contact" class="btn btn-primary btn-sm">Enquire</a>'),

    # 푸터
    ('<span class="logo">강산재</span>', '<span class="logo">Gangsanjae</span>'),
    ('''        자연숲속 한옥호텔 강산재<br>
        강원특별자치도 홍천군 서면 고루개길 110<br>
        <a href="tel:01090277662">010-9027-7662</a> &nbsp;·&nbsp; 카카오톡 ID : ksanj''',
     f'''        Gangsanjae — a hanok retreat in the forest<br>
        110 Gorugae-gil, Seo-myeon, Hongcheon-gun, Gangwon State, Republic of Korea<br>
        <a href="{TEL_HREF}">{TEL_TEXT}</a> &nbsp;·&nbsp; KakaoTalk ID : ksanj'''),
    ('<a href="https://www.instagram.com/hanokhotel_kangsanjae/" target="_blank" rel="noopener">인스타그램 @hanokhotel_kangsanjae</a>',
     '<a href="https://www.instagram.com/hanokhotel_kangsanjae/" target="_blank" rel="noopener">Instagram @hanokhotel_kangsanjae</a>'),
    ('<a href="#">네이버 스마트플레이스</a>', '<a href="#">Naver Place</a>'),
    ('<a href="#">에어비앤비</a>', '<a href="#">Airbnb</a>'),
    ('<span>[사업자정보 확인 필요]</span>', '<span>[Business registration details to be added]</span>'),
    ('<a href="#">이용약관</a><a href="#">개인정보처리방침</a>',
     '<a href="#">Terms</a><a href="#">Privacy</a>'),

    # 모바일 하단 바
    ('<a href="https://open.kakao.com/" class="kakao">카카오톡 문의</a>',
     f'<a href="{enquiry_href()}" class="kakao" target="_blank" rel="noopener">{enquiry_label()}</a>'),
    ('<a href="#booking" class="book">예약 문의</a>', '<a href="#booking" class="book">Enquire</a>'),
    ('<a href="/#booking" class="book">예약 문의</a>', '<a href="/en#booking" class="book">Enquire</a>'),
    ('<a href="#contact" class="book">예약 문의</a>', '<a href="#contact" class="book">Enquire</a>'),

    # 공통 CTA 버튼
    ('<a href="https://open.kakao.com/" class="btn btn-gold">카카오톡 문의 (ID : ksanj)</a>',
     f'<a href="{enquiry_href()}" class="btn btn-gold" target="_blank" rel="noopener">{enquiry_label()}</a>'),
    ('<a href="/info" class="btn btn-ghost">이용안내 보기</a>',
     '<a href="/en/info" class="btn btn-ghost">Rates &amp; information</a>'),
]

# ---------------------------------------------------------------- 페이지별 문구
PAGE = {}

PAGE["index.html"] = [
    ("<title>홍천 한옥 펜션 강산재 — 4만 평 숲속 대목장 한옥 독채</title>",
     "<title>Gangsanjae — A Private Hanok Estate in the Forests of Hongcheon, Korea</title>"),
    ('<meta name="description" content="강원 홍천 4만 평 숲속 한옥 독채 강산재. 국내 최고 대목장이 지은 전통 한옥에서 최대 12인까지, 맨발 황톳길과 한의학 박사 건강 상담이 있는 치유 스테이.">',
     '<meta name="description" content="A whole traditional hanok on 33 acres of private Korean forest. Built by a daemokjang master carpenter, sleeps up to 12. Barefoot clay paths, ondol floors, and a filming location for Netflix’s XO, Kitty.">'),
    ('<meta property="og:title" content="홍천 한옥 펜션 강산재 — 4만 평 숲속 대목장 한옥 독채">',
     '<meta property="og:title" content="Gangsanjae — A Private Hanok Estate in the Forests of Hongcheon, Korea">'),
    ('<meta property="og:description" content="4만 평 숲이 통째로 정원인, 대목장이 지은 치유 한옥. 강원 홍천 강산재.">',
     '<meta property="og:description" content="Thirty-three acres of forest, and all of it yours for the day. A master-built hanok in Hongcheon, Korea.">'),
    ("<title>", "<title>"),  # no-op guard

    # 히어로
    ('<p class="hero-eyebrow hero-fade f1">GANGSANJAE&nbsp;&nbsp;·&nbsp;&nbsp;HONGCHEON</p>',
     '<p class="hero-eyebrow hero-fade f1">GANGSANJAE&nbsp;&nbsp;·&nbsp;&nbsp;HONGCHEON, KOREA</p>'),
    ('<h1 class="hero-fade f2">4만 평 숲이,<br>당신 혼자의 정원이 됩니다</h1>',
     '<h1 class="hero-fade f2">Thirty-three acres of forest,<br>and no one in it but you</h1>'),
    ('<p class="hero-sub hero-fade f3">보이는 이 전부가 오늘 하루 당신의 것입니다<span class="sub2"><br>국내 최고 대목장이 지은 한옥 독채, 강원 홍천 강산재</span></p>',
     '<p class="hero-sub hero-fade f3">Everything you can see is yours for the day<span class="sub2"><br>A whole hanok raised by a master carpenter — Hongcheon, Gangwon</span></p>'),
    ('<a href="/space" class="btn btn-ghost">공간 둘러보기</a>',
     '<a href="/en/space" class="btn btn-ghost">See the house</a>'),
    ('<a href="#booking" class="btn btn-primary">카카오톡 예약 문의</a>',
     '<a href="#booking" class="btn btn-primary">Enquire about dates</a>'),

    # 배지
    ('<li><span class="k">대목장의 손</span><span class="s">국내 최고 대목장 건축</span></li>',
     '<li><span class="k">Master-built</span><span class="s">Raised by a daemokjang carpenter</span></li>'),
    ('<li><span class="k">XO, Kitty</span><span class="s">Netflix 시즌2 촬영지</span></li>',
     '<li><span class="k">XO, Kitty</span><span class="s">Netflix season 2 filming location</span></li>'),
    ('<li><span class="k">4.94</span><span class="s">숙소 평점 / 5.0</span></li>',
     '<li><span class="k">4.94</span><span class="s">Guest rating / 5.0</span></li>'),
    ('<li><span class="k">73</span><span class="s">누적 후기 수</span></li>',
     '<li><span class="k">73</span><span class="s">Reviews to date</span></li>'),

    # 인터루드
    ('<h2 class="reveal">문을 닫으면,<br>여기서부터는 아무도 없습니다</h2>',
     '<h2 class="reveal">Close the gate,<br>and the rest of the world stops here</h2>'),
    ('<p class="reveal d1">한 팀만 머무는 독채입니다. 옆방도, 지나가는 사람도, 프런트도 없습니다.<br>처마 밑에 앉아 해가 넘어가는 것만 보셔도 하루가 갑니다.</p>',
     '<p class="reveal d1">One booking at a time. No neighbouring room, no passers-by, no front desk.<br>Sit under the eaves and watch the sun go down — that can be the whole day.</p>'),
    ('<h2 class="reveal">이 안에 다른 손님은 없습니다</h2>',
     '<h2 class="reveal">There are no other guests inside</h2>'),
    ('<p class="reveal d1">본채 · 별채 · 정자 · 마당 · 장독대 · 숲길까지, 한 팀이 통째로 씁니다</p>',
     '<p class="reveal d1">Main house, annex, pavilion, lawn, jar terrace, forest trails — one party has all of it</p>'),

    # 영상
    ('<h2 class="reveal d1">영상으로 먼저 걸어보십시오</h2>',
     '<h2 class="reveal d1">Walk it first, on film</h2>'),
    ('<p class="lead reveal d2">사진에 다 담기지 않는 공기와 소리가 있습니다.</p>',
     '<p class="lead reveal d2">There is air and sound here that photographs cannot hold.</p>'),
    ('title="강산재 소개 영상"', 'title="Gangsanjae introduction film"'),

    # 4대 강점
    ('<h2 class="reveal d1">강산재가 다른 이유</h2>', '<h2 class="reveal d1">Why Gangsanjae</h2>'),
    ('<h3>대목장의 한옥</h3>\n      <p>국내 최고 대목장이 손으로 지어 올린 전통 한옥. 못이 아니라 결구로 세운 집입니다.</p>',
     '<h3>A master’s hanok</h3>\n      <p>Raised by hand by a daemokjang — one of Korea’s designated master carpenters. Joined timber, not a single nail.</p>'),
    ('<h3>4만 평의 독채</h3>\n      <p>옆방 소음이 없습니다. 숲 전체가 오늘 하루 당신의 마당입니다.</p>',
     '<h3>33 acres, all yours</h3>\n      <p>No noise through the wall. For one day the whole forest is your garden.</p>'),
    ('<h3>치유의 동선</h3>\n      <p>황토 온돌방, 맨발 황톳길, 치유 연못. 걷는 것만으로 회복되는 구조입니다.</p>',
     '<h3>Built for recovery</h3>\n      <p>Clay-floored ondol rooms, a barefoot loess path, a still pond. The walking itself does the work.</p>'),
    ('<h3>3대가 함께</h3>\n      <p>침실 5 · 욕실 2 · 10인 식탁. 최대 12인까지 한 채에서 머뭅니다.</p>',
     '<h3>Room for three generations</h3>\n      <p>Five bedrooms, two baths, a table for ten. Up to 12 guests under one roof.</p>'),

    # 갤러리
    ('<h2 class="reveal d1">다섯 개의 방, 하나의 집</h2>', '<h2 class="reveal d1">Five rooms, one house</h2>'),
    ('<a href="/space" class="more reveal d2">공간 전체 보기 →</a>',
     '<a href="/en/space" class="more reveal d2">See every room →</a>'),
    ('<figcaption class="cap">거실 — 통창 너머로 마당이 그대로 들어옵니다</figcaption>',
     '<figcaption class="cap">Living room — the garden arrives through the glass</figcaption>'),
    ('<figcaption class="cap">황토 온돌방 — 치유의 중심</figcaption>',
     '<figcaption class="cap">Clay ondol room — the heart of the stay</figcaption>'),
    ('<figcaption class="cap">차실 — 창 전체가 마당입니다</figcaption>',
     '<figcaption class="cap">Tea room — the whole window is garden</figcaption>'),
    ('<figcaption class="cap">다락방 — 아이들이 가장 좋아하는 방</figcaption>',
     '<figcaption class="cap">Attic room — the children never leave it</figcaption>'),
    ('<figcaption class="cap">주방 — 10인 식탁</figcaption>',
     '<figcaption class="cap">Kitchen — a table that seats ten</figcaption>'),

    # 하루의 시간
    ('<h2 class="reveal d1">하루가 이렇게 흘러갑니다</h2>', '<h2 class="reveal d1">How a day passes here</h2>'),
    ('<p class="lead reveal d2">특별히 할 일을 만들지 않아도 됩니다. 해가 움직이는 대로 자리를 옮기시면 됩니다.</p>',
     '<p class="lead reveal d2">You do not need to plan anything. Simply move as the sun moves.</p>'),
    ('<span class="k">오후, 정자에 앉습니다</span>\n        <span class="d">산이 정면으로 보이는 자리. 여기서 대부분의 시간이 지나갑니다.</span>',
     '<span class="k">Afternoon, in the pavilion</span>\n        <span class="d">The seat that faces the mountain. Most of the day goes here.</span>'),
    ('<span class="k">저녁, 불이 하나씩 켜집니다</span>\n        <span class="d">창호에 불이 들어오면 집이 완전히 다른 얼굴이 됩니다.</span>',
     '<span class="k">Dusk, the lamps come on one by one</span>\n        <span class="d">Light behind the paper screens gives the house another face entirely.</span>'),
    ('<span class="k">밤, 장독대 앞에 불을 피웁니다</span>\n        <span class="d">의자를 끌어다 놓고 앉으면, 아무도 먼저 일어나지 않습니다.</span>',
     '<span class="k">Night, a fire by the jars</span>\n        <span class="d">Pull up a chair and nobody is the first to stand up.</span>'),
]

PAGE["index.html"] += [
    # 치유
    ('<h2 class="reveal d1">머무는 것이 곧 치유입니다</h2>',
     '<h2 class="reveal d1">Staying is the treatment</h2>'),
    ('<h3>한의학 박사 1:1 건강 상담</h3>\n          <p>서울에서 한의원을 운영하는 한의학 박사가 직접 상담합니다. (사전 예약 필수)</p>',
     '<h3>One-to-one consultation with a doctor of Korean medicine</h3>\n          <p>A doctor of Korean medicine who runs a clinic in Seoul sees guests personally. Booking required in advance.</p>'),
    ('<h3>맨발 황톳길 걷기</h3>\n          <p>숲으로 이어지는 황토 산책로에서 맨발로 걷습니다.</p>',
     '<h3>Barefoot on the clay path</h3>\n          <p>A packed loess trail runs from the garden into the forest. Walk it with your shoes off.</p>'),
    ('<h3>차실 다도</h3>\n          <p>전통 차실에서 차 한 잔의 시간을 가집니다.</p>',
     '<h3>Tea in the tea room</h3>\n          <p>An hour of tea, prepared the traditional way.</p>'),
    ('<h3>불멍과 캠프파이어</h3>\n          <p>달과 별 아래, 아무 말 없이 불을 봅니다.</p>',
     '<h3>Fire-gazing</h3>\n          <p>Under the moon, watching the flames, saying nothing.</p>'),

    # 사계
    ('<h2 class="reveal d1">같은 마당이, 네 번 다른 곳이 됩니다</h2>',
     '<h2 class="reveal d1">The same garden, four different places</h2>'),
    ('<p class="lead reveal d2">언제 오시느냐에 따라 전혀 다른 하루가 됩니다. 한 번 다녀가신 분들이 다른 계절에 다시 오시는 이유입니다.</p>',
     '<p class="lead reveal d2">When you come changes what you get. It is why guests return in another season.</p>'),
    ('<span class="k">봄</span><span class="d">마당까지 초록이 내려옵니다</span>',
     '<span class="k">Spring</span><span class="d">Green comes all the way down to the lawn</span>'),
    ('<span class="k">여름</span><span class="d">연못에 수련이 오릅니다</span>',
     '<span class="k">Summer</span><span class="d">Water lilies open on the pond</span>'),
    ('<span class="k">가을</span><span class="d">수국이 마르고 호박이 익습니다</span>',
     '<span class="k">Autumn</span><span class="d">Hydrangeas dry and the pumpkins ripen</span>'),
    ('<span class="k">겨울</span><span class="d">장독마다 눈이 앉고 등이 켜집니다</span>',
     '<span class="k">Winter</span><span class="d">Snow settles on every jar and the lanterns come on</span>'),

    # 아침상
    ('<h2>아침은,<br>창밖에 안개가 낀 채로 시작합니다</h2>',
     '<h2>Morning begins<br>with mist still on the garden</h2>'),
    ('<p>10인 식탁에 아침이 차려집니다. 커다란 창 너머로 마당이 그대로 보이고, 밤새 내려앉은 안개가 천천히 걷힙니다. 서둘러 나갈 일이 없는 아침입니다.</p>',
     '<p>Breakfast is laid on the table for ten. Through the wide window the garden sits there, and the mist that came down overnight lifts slowly. There is nowhere you need to be.</p>'),
    ('<p class="meta">조식 제공 여부 및 가격 <span class="tbc">[확인 필요]</span></p>',
     '<p class="meta">Breakfast availability and price <span class="tbc">[to be confirmed]</span></p>'),

    # 파노라마
    ('<h2 class="reveal">마당에 상을 펴면, 그 자체로 잔치가 됩니다</h2>',
     '<h2 class="reveal">Set a table on the lawn and it becomes a feast</h2>'),
    ('<p class="reveal d1">12인이 한 상에 앉습니다. 옆에는 히노키 욕조가 있습니다</p>',
     '<p class="reveal d1">Twelve at one table, with a hinoki tub beside it</p>'),

    # 호스트
    ('<h2 class="reveal d1">화가가 짓고 있는,<br>아직 끝나지 않은 작품</h2>',
     '<h2 class="reveal d1">A painter’s work,<br>still unfinished</h2>'),
    ('<blockquote class="reveal d2">“산이 좋아 산으로 들어온 사람입니다. 삶을 예술로 여기며, 삶의 공간을 예술로 승화시키고자 합니다. 4만 평 숲속 강산재를 저의 작품으로 만들고 있습니다. 그 예술의 일부가 되실 수 있습니다.”</blockquote>',
     '<blockquote class="reveal d2">“I loved the mountains, so I came to live in them. I treat life as art, and I want the space I live in to become art too. Gangsanjae, in these thirty-three acres of forest, is the work I am still making. You are welcome to become part of it.”</blockquote>'),
    ('<p class="sign reveal d3">강산재 주인, 화가 · 경희대학교 미술대학 석사</p>',
     '<p class="sign reveal d3">Owner of Gangsanjae — painter, MFA, Kyung Hee University</p>'),

    # 후기
    ('<h2 class="reveal d1">다녀가신 분들의 말</h2>', '<h2 class="reveal d1">What guests say</h2>'),
    ('<li><span class="val">4.94</span><span class="key">종합</span></li>',
     '<li><span class="val">4.94</span><span class="key">Overall</span></li>'),
    ('<li><span class="val">4.9</span><span class="key">청결도</span></li>',
     '<li><span class="val">4.9</span><span class="key">Cleanliness</span></li>'),
    ('<li><span class="val">5.0</span><span class="key">소통</span></li>',
     '<li><span class="val">5.0</span><span class="key">Communication</span></li>'),
    ('<li><span class="val">4.9</span><span class="key">위치</span></li>',
     '<li><span class="val">4.9</span><span class="key">Location</span></li>'),
    ('<p>조용하면서 힐링하기 좋은 멋진 한옥 펜션입니다. 거위 구경, 블루베리 따기 체험, 모래 놀이, 캠프파이어 등등 안에서 즐길 것들이 너무 많습니다. 2박 3일간 너무 즐겁게 지내다 갔고, 같이 갔던 어른들은 물론이고 아이들도 엄청 만족하네요.</p>\n      <span class="who">아이 동반 가족 여행 · 2박 3일</span>',
     '<p>A beautiful, quiet hanok — perfect for switching off. Geese to watch, blueberry picking, a sandpit, a campfire; there is so much to do without leaving. We had a wonderful three days, and the children were every bit as happy as the adults.</p>\n      <span class="who">Family stay with children · 3 days</span>'),
    ('<p>믿고 보는 강산재, 벌써 다섯 번째 방문이고 올 때마다 만족 대만족입니다. 아이들은 옥탑방에서 꺄르르 웃고 떠들고, 함께 온 부모님들도 강산재의 풍경에 흠뻑 취해 여유롭고 풍요로운 주말을 보냈습니다. 올 때마다 진정한 럭셔리가 무엇인지 느끼며 푹 쉬다 갑니다.</p>\n      <span class="who">다섯 번째 방문 · 두 가족 친목 모임</span>',
     '<p>Gangsanjae never disappoints — this was our fifth visit and it is better every time. The children shrieked with laughter up in the attic room, and the grandparents fell completely under the spell of the view. Every time we come we understand again what real luxury means.</p>\n      <span class="who">Fifth visit · two families together</span>'),
    ('<p>어머니 팔순 기념으로 16명 대가족이 방문하여 행복한 시간을 보냈습니다. 사장님 배려로 가족 모두 편안하고 즐겁게 행사를 마쳤어요! 웰컴티부터 와인 선물, 정성 가득한 아침식사까지 세심한 서비스에 감사드립니다.</p>\n      <span class="who">어머니 팔순 · 16인 가족모임</span>',
     '<p>Sixteen of us came for my mother’s eightieth birthday and it was a joy from start to finish. The owner looked after every detail — a welcome tea, a gift of wine, a breakfast made with real care.</p>\n      <span class="who">80th birthday · family of 16</span>'),
    ('<p class="review-note reveal">에어비앤비 후기 18개 · 네이버 예약 리뷰 55개<br>후기에서 가장 많이 언급된 단어 — “친절함” 16회 · “가족” 14회</p>',
     '<p class="review-note reveal">18 Airbnb reviews · 55 Naver booking reviews<br>Most mentioned words — “kind” 16 times · “family” 14 times</p>'),

    # 예약 CTA
    ('<h2 class="reveal">산으로 오십시오. 강산재입니다.</h2>',
     '<h2 class="reveal">Come to the mountains. This is Gangsanjae.</h2>'),
    ('<p class="reveal d1">1박 750,000원부터 · 입실 오후 3시<br>홈페이지에서 직접 예약하시면 바비큐 세트(4~8인)를 무료로 준비해 드립니다.</p>',
     '<p class="reveal d1">From KRW 750,000 per night · check-in 3 pm<br>Book with us directly and the barbecue set for 4–8 guests is on the house.</p>'),
    ('<a href="/info" class="btn btn-ghost">예약 가능일 확인</a>',
     '<a href="/en/info" class="btn btn-ghost">Rates &amp; availability</a>'),
]

# ---------------------------------------------------------------- 이미지 대체 텍스트
ALT = {
    "10인이 앉는 원목 식탁과 강산재 주방": "The kitchen at Gangsanjae with its solid-wood table for ten",
    "10인이 앉는 원목 식탁과 주방": "A solid-wood dining table for ten beside the kitchen",
    "가을 단풍에 둘러싸인 수타사 대적광전": "Sutasa temple’s main hall surrounded by autumn colour",
    "강산재 본채 정면의 전통 창호와 장독": "Traditional lattice doors and storage jars at the front of the main house",
    "강산재 본채 측면과 잔디마당": "The side of the main house and the lawn",
    "강산재 위치 지도 — 강원특별자치도 홍천군 서면 고루개길 110": "Map showing Gangsanjae at 110 Gorugae-gil, Seo-myeon, Hongcheon-gun, Gangwon State",
    "넓은 잔디마당에 놓인 야외 긴 테이블과 히노키 욕조": "A long outdoor table and a hinoki tub on the wide lawn",
    "눈 내린 밤, 등불이 켜진 장독대": "Lanterns lit over the jar terrace on a snowy night",
    "돌 세면대와 욕조가 있는 강산재 욕실": "A bathroom with a stone basin and a deep tub",
    "돌담과 잔디가 있는 강산재 정원 마당": "The garden with its stone wall and lawn",
    "마당을 두르고 늘어선 장독대": "Rows of fermentation jars ringing the garden",
    "마당의 정자와 야외 긴 테이블": "The pavilion and the long outdoor table on the lawn",
    "마당의 정자와 야외 테이블": "The pavilion and outdoor table on the lawn",
    "맑은 날, 솟을대문과 잔디마당": "The raised main gate and the lawn on a clear day",
    "밤, 창마다 불이 들어온 강산재 본채": "The main house at night with every window lit",
    "산을 등지고 앉은 강산재 전경": "Gangsanjae set against the mountain",
    "산을 등지고 앉은 강산재 한옥과 장독대 전경": "The hanok and its jar terrace with the mountain behind",
    "산을 배경으로 풀밭에 서 있는 알파카들": "Alpacas standing on grass with mountains behind",
    "서까래가 드러난 다락방의 침대와 요": "The attic room with exposed rafters, a bed and floor bedding",
    "소나무 사이로 이어지는 강산재의 황토 산책로": "The clay walking path running between the pines",
    "소나무 사이로 이어지는 황토 산책로": "A clay path running between the pines",
    "솟을대문과 맷돌 디딤돌이 놓인 잔디마당": "The raised gate and millstone stepping stones on the lawn",
    "수련이 떠 있는 강산재 치유 연못": "Water lilies floating on the pond",
    "안개가 내려앉은 산과 강산재 정자 지붕": "Mist over the mountain and the pavilion roof",
    "야외 긴 테이블과 히노키 욕조가 놓인 잔디마당": "The lawn with its long outdoor table and hinoki tub",
    "요를 깔아둔 강산재 황토 온돌방": "The clay-floored ondol room with bedding laid out",
    "요를 깔아둔 강산재 황토 온돌방과 창밖 풍경": "The clay ondol room with bedding laid out and the view beyond",
    "원목 기둥이 이어지는 강산재 실내 복도": "The interior corridor lined with timber posts",
    "장독대 앞 화로에 불이 타오르는 밤": "A fire burning in the pit in front of the jar terrace at night",
    "장독대 옆 화로와 장작이 쌓인 캠프파이어 구역": "The campfire area beside the jar terrace, firewood stacked",
    "전통 약장과 통나무 좌탁이 놓인 사랑방": "The sarangbang with its traditional medicine chest and log table",
    "전통 약장과 통나무 좌탁이 놓인 상담 공간": "The consultation room with its traditional medicine chest and log table",
    "정자 안 원목 테이블과 그 너머로 펼쳐진 산": "The table inside the pavilion and the mountains beyond",
    "정자가 있는 강산재의 넓은 잔디마당": "Gangsanjae’s wide lawn with its pavilion",
    "정자가 있는 넓은 잔디마당": "A wide lawn with a pavilion",
    "정자에서 바라본 가을 마당과 마른 수국": "The autumn garden and dried hydrangeas seen from the pavilion",
    "주방 옆에 놓인 피아노": "A piano beside the kitchen",
    "창밖으로 안개 낀 마당이 보이는 원목 식탁 위의 아침 상차림": "Breakfast laid on the wooden table, mist on the garden outside",
    "처마 아래에서 바라본 마당과 산": "The garden and mountains seen from under the eaves",
    "통나무를 깎아 만든 다락방 계단": "Attic stairs carved from a single log",
    "통창으로 마당이 보이는 강산재 거실과 원목 좌탁": "The living room and low wooden table, garden filling the window",
    "통창으로 마당이 보이는 강산재 본채 거실": "The living room of the main house, garden filling the window",
    "통창으로 마당이 보이는 차실의 원목 좌탁": "The tea room’s low wooden table with the garden beyond",
    "하늘에서 내려다본 강산재 전체 부지": "Gangsanjae’s grounds seen from the air",
    "하늘에서 내려다본 강산재 전체 부지와 잔디마당": "Gangsanjae’s grounds and lawn seen from the air",
    "한옥 너머로 이어지는 숲과 산봉우리": "Forest and peaks stretching away beyond the hanok",
    "한지 벽과 원목 선반이 있는 강산재 침실": "A bedroom with paper-lined walls and timber shelving",
    "해질 무렵 불이 켜진 강산재 본채": "The main house lit at dusk",
    "해질 무렵의 강산재 마당과 별채": "The garden and annex at sunset",
    "홍천강이 휘감아 도는 팔봉산 항공 전경": "Palbongsan and the Hongcheon river seen from the air",
    "황토 바닥 위에 놓인 퀸 침대와 창호": "A queen bed on a clay floor beside lattice doors",
}

PAGE["space.html"] = [
    ("<title>공간 — 홍천 독채 한옥 강산재 | 침실 5 · 차실 · 4만 평 숲</title>",
     "<title>The Space — Gangsanjae | 5 bedrooms, a tea room, 33 acres of forest</title>"),
    ('<meta name="description" content="강산재의 공간 안내. 황토 온돌방과 돌침대 침실, 전통 차실, 10인 식탁 주방과 4만 평 숲 트레킹로까지. 홍천 독채 펜션 강산재의 실내외 시설 전체를 소개합니다.">',
     '<meta name="description" content="Five bedrooms, two baths, a table for ten. Clay ondol rooms, a tea room, a pavilion and a terrace of fermentation jars — every corner of Gangsanjae.">'),
    ('<meta property="og:title" content="공간 — 홍천 독채 한옥 강산재">',
     '<meta property="og:title" content="The Space — Gangsanjae">'),
    ('<meta property="og:description" content="침실 5 · 욕실 2 · 차실 1 · 10인 식탁. 최대 12인이 한 채에서 머무는 한옥 독채.">',
     '<meta property="og:description" content="Five bedrooms, two baths, a table for ten. Every corner of Gangsanjae.">'),
    ("<h1>공간</h1>", "<h1>The Space</h1>"),
    ("<p>독채 1동 · 침실 5 · 침대 3 · 이불세트 6 · 욕실 2</p>",
     "<p>One private house · 5 bedrooms · 3 beds · 6 floor-bedding sets · 2 bathrooms</p>"),
    ("<h2>실내</h2>", "<h2>Indoors</h2>"),
    ("<h3>본채 거실</h3>\n        <p>우물마루와 통창. 앉은 자리에서 마당과 숲이 한 화면으로 들어옵니다.</p>",
     "<h3>Living room</h3>\n        <p>A traditional plank floor and a wall of glass. Sit down and the garden and forest arrive as one picture.</p>"),
    ("<h3>주방</h3>\n        <p>10인용 식탁, 대가족 취사 가능</p>",
     "<h3>Kitchen</h3>\n        <p>A table for ten, and room to cook for a large family</p>"),
    ("<h3>욕실 2개</h3>\n        <p>12인이 머물러도 아침이 밀리지 않도록 두 곳에 두었습니다.</p>",
     "<h3>Two bathrooms</h3>\n        <p>Two of them, so that mornings do not queue even with twelve in the house.</p>"),
    ('<h2 style="font-size:26px;">다섯 개의 침실</h2>', '<h2 style="font-size:26px;">Five bedrooms</h2>'),
    ("<h3>침실 1</h3><p>킹 사이즈 돌침대 — 원적외선, 깊은 숙면</p>",
     "<h3>Bedroom 1</h3><p>King-size stone bed — far-infrared warmth, deep sleep</p>"),
    ("<h3>침실 2</h3><p>퀸 침대 — 부모님과 부부를 위한 방</p>",
     "<h3>Bedroom 2</h3><p>Queen bed — for grandparents or a couple</p>"),
    ("<h3>침실 3 · 황토 온돌방</h3><p>강산재의 핵심 치유 공간</p>",
     "<h3>Bedroom 3 · clay ondol room</h3><p>The heart of the stay</p>"),
    ("<h3>침실 4·5 · 다락방</h3><p>아이들이 가장 오래 머무는 곳</p>",
     "<h3>Bedrooms 4 &amp; 5 · attic</h3><p>Where the children spend the most time</p>"),
    ("<h3>차실</h3><p>전통 다도를 위한 별도 공간</p>",
     "<h3>Tea room</h3><p>A separate room for taking tea the traditional way</p>"),
    ("<h3>사랑방</h3><p>전통 약장과 통나무 좌탁. 상담이 이루어지는 자리입니다.</p>",
     "<h3>Sarangbang</h3><p>A traditional medicine chest and a log table. This is where consultations happen.</p>"),
    ("<h3>창호와 문</h3><p>손으로 짠 전통 창살, 계절마다 다른 빛이 들어옵니다.</p>",
     "<h3>Lattice doors</h3><p>Hand-joined traditional latticework. Each season lets in a different light.</p>"),
    ("<h3>복도</h3><p>방과 방 사이를 잇는 마루. 걸을 때마다 나무 소리가 납니다.</p>",
     "<h3>Corridor</h3><p>The plank floor between the rooms. It sounds under your feet.</p>"),
    ("<h3>다락 계단</h3><p>통나무를 통째로 깎아 만든 계단입니다.</p>",
     "<h3>Attic stairs</h3><p>Carved from a single log.</p>"),
    ("<h3>피아노</h3><p>주방 옆, 누구든 앉아서 칠 수 있습니다.</p>",
     "<h3>Piano</h3><p>Beside the kitchen. Anyone may sit down and play.</p>"),
    ("<h2>실외</h2>", "<h2>Outdoors</h2>"),
    ("<h3>넓은 정원 마당</h3>", "<h3>The garden</h3>"),
    ("<h3>잔디마당</h3>", "<h3>The lawn</h3>"),
    ("<h3>캠프파이어 존</h3>", "<h3>Campfire area</h3>"),
    ("<h3>정자와 야외 테이블</h3>", "<h3>Pavilion and outdoor table</h3>"),
    ("<h3>4만 평 숲 트레킹로</h3>", "<h3>Forest trails across 33 acres</h3>"),
    ("<h3>툇마루와 전망</h3>", "<h3>The veranda and the view</h3>"),
    ("<h3>치유 연못</h3>", "<h3>The pond</h3>"),
    ("<h3>황토 맨발 산책마당</h3>", "<h3>Barefoot clay path</h3>"),
    ("<h3>솟을대문과 디딤돌</h3>", "<h3>Raised gate and stepping stones</h3>"),
    ("<h3>장독대</h3>", "<h3>Jar terrace</h3>"),
    ("<h3>정자 마당</h3>", "<h3>Pavilion lawn</h3>"),
    ("<h3>야외 히노키 욕조</h3>", "<h3>Outdoor hinoki tub</h3>"),
    ('<span class="note" style="letter-spacing:.14em;">그 밖에</span>\n    <span>바비큐 존</span><span>어린이 모래놀이마당</span><span>투호 · 그네</span><span>4만 평 숲 트레킹로</span>',
     '<span class="note" style="letter-spacing:.14em;">Also</span>\n    <span>Barbecue area</span><span>Children’s sandpit</span><span>Traditional games · swing</span><span>33 acres of forest trails</span>'),
    ("<h2>편의시설</h2>", "<h2>Amenities</h2>"),
    ("<span>와이파이</span>", "<span>Wi-Fi</span>"),
    ("<span>에어컨</span>", "<span>Air conditioning</span>"),
    ("<span>세탁기</span>", "<span>Washing machine</span>"),
    ("<span>무료 건조기</span>", "<span>Free dryer</span>"),
    ("<span>업무 전용 공간</span>", "<span>Dedicated workspace</span>"),
    ("<span>부지 내 무료 주차</span>", "<span>Free parking on site</span>"),
    ("<span>전용 뒷마당</span>", "<span>Private back garden</span>"),
    ("<span>외부 보안 카메라</span>", "<span>Exterior security cameras</span>"),
    ('<p class="note" style="margin-top:34px;">※ 에어비앤비 등록 편의시설 총 65종 — <span class="tbc">[전체 목록 확인 필요]</span></p>',
     '<p class="note" style="margin-top:34px;">65 amenities are listed on our Airbnb page — <span class="tbc">[full list to be added]</span></p>'),
    ('<h2 class="reveal">이 집을 하루 통째로 쓰십시오</h2>',
     '<h2 class="reveal">Take the whole house for a day</h2>'),
    ('<p class="reveal d1">최대 12인 · 8인 이상은 사전 상담 후 예약</p>',
     '<p class="reveal d1">Up to 12 guests · parties over 8 by prior arrangement</p>'),
]

PAGE["healing.html"] = [
    ("<title>치유 프로그램 — 강원도 웰니스 스테이 강산재 | 맨발 황톳길·한방 상담</title>",
     "<title>Healing — Gangsanjae | Barefoot clay paths &amp; Korean medicine</title>"),
    ('<meta name="description" content="한의학 박사 1:1 건강 상담, 맨발 황톳길 걷기, 차실 다도, 불멍까지. 강원 홍천 4만 평 숲속 한옥 강산재에서 1박 2일 동안 이어지는 회복의 시간을 안내합니다.">',
     '<meta name="description" content="A one-to-one consultation with a doctor of Korean medicine, a barefoot clay path, tea in the tea room, and a fire at night.">'),
    ('<meta property="og:title" content="치유 프로그램 — 강원도 웰니스 스테이 강산재">',
     '<meta property="og:title" content="Healing — Gangsanjae">'),
    ('<meta property="og:description" content="머무는 것이 곧 치유입니다. 한의학 박사 상담과 맨발 황톳길이 있는 한옥 스테이.">',
     '<meta property="og:description" content="A healing stay with barefoot clay paths and a doctor of Korean medicine on hand.">'),
    ("<h1>치유</h1>", "<h1>Healing</h1>"),
    ("<p>강산재에서만 가능한 회복의 시간</p>", "<p>Recovery of a kind only possible here</p>"),
    ("<h2>한의학 박사<br>1:1 건강 상담</h2>",
     "<h2>One-to-one consultation<br>with a doctor of Korean medicine</h2>"),
    ("<p>서울에서 한의원을 운영하는 한의학 박사가 강산재에 머무는 동안 직접 상담해 드립니다. 체질과 생활 습관을 함께 살펴, 돌아가신 뒤에도 이어갈 수 있는 방향을 안내합니다.</p>",
     "<p>A doctor of Korean medicine who runs a clinic in Seoul sees guests personally during their stay. You will go through your constitution and daily habits together, and leave with something you can keep doing at home.</p>"),
    ("<span>사전 예약 필수</span>\n        <span>비용 — [비용 확인 필요]</span>",
     "<span>Advance booking required</span>\n        <span>Fee — [to be confirmed]</span>"),
    ('<a href="https://open.kakao.com/" class="btn btn-gold">상담 예약 문의</a>',
     f'<a href="{enquiry_href()}" class="btn btn-gold" target="_blank" rel="noopener">Ask about a consultation</a>'),
    ("<h3>맨발 황톳길</h3>\n        <p>숲으로 이어지는 황토 산책로에서 맨발로 걷습니다.</p>",
     "<h3>Barefoot clay path</h3>\n        <p>A packed loess trail into the forest. Walk it with your shoes off.</p>"),
    ("<h3>차 한 잔의 시간</h3>\n        <p>전통 차실과 정자에서 차를 마십니다.</p>",
     "<h3>An hour for tea</h3>\n        <p>Taken in the tea room, or out in the pavilion.</p>"),
    ("<h3>불멍</h3>\n        <p>달과 별 아래, 아무 말 없이 불을 봅니다.</p>",
     "<h3>Fire-gazing</h3>\n        <p>Under the moon and stars, watching the flames, saying nothing.</p>"),
    ("<h3>전통 놀이 체험</h3>\n        <p>바둑, 윷놀이, 투호를 함께 즐깁니다.</p>",
     "<h3>Traditional games</h3>\n        <p>Baduk, yut, and tuho — played together.</p>"),
    ('<h2 class="reveal">몸이 먼저 알아차립니다</h2>', '<h2 class="reveal">The body notices first</h2>'),
    ('<p class="reveal d1">맨발로 황톳길을 걷고, 황토방에서 자고, 아침에 상담을 받습니다.<br>하루 만에 달라지는 것이 있습니다.</p>',
     '<p class="reveal d1">Walk the clay path barefoot, sleep on a warm clay floor, sit down with the doctor in the morning.<br>One day is enough to feel the difference.</p>'),
    ('<h2 class="reveal d1">1박 2일 치유 일정 예시</h2>',
     '<h2 class="reveal d1">A sample one-night stay</h2>'),
    ('<span class="act">체크인 및 차 한 잔</span>', '<span class="act">Check in, tea</span>'),
    ('<span class="act">맨발 황톳길</span>', '<span class="act">Barefoot clay path</span>'),
    ('<span class="act">바비큐</span>', '<span class="act">Barbecue</span>'),
    ('<span class="act">불멍</span>', '<span class="act">Fire by the jars</span>'),
    ('<span class="act">황토방 취침</span>', '<span class="act">Sleep on the clay floor</span>'),
    ('<span class="act">조식</span>', '<span class="act">Breakfast</span>'),
    ('<span class="act">건강 상담</span>', '<span class="act">Health consultation</span>'),
    ('<span class="act">체크아웃</span>', '<span class="act">Check out</span>'),
    ('<p class="note" style="margin-top:26px;">※ 입실 오후 3시 · 퇴실 오전 11시 기준으로 구성한 예시 일정입니다.</p>',
     '<p class="note" style="margin-top:26px;">A sample schedule, based on a 3 pm check-in and an 11 am check-out.</p>'),
    ('<h2 class="reveal">상담은 사전 예약제입니다</h2>',
     '<h2 class="reveal">Consultations are by advance booking</h2>'),
    ('<p class="reveal d1">머무시는 날짜를 알려주시면 가능한 시간을 안내해 드립니다.</p>',
     '<p class="reveal d1">Tell us your dates and we will let you know the times available.</p>'),
]

PAGE["info.html"] = [
    ("<title>이용안내 · 오시는 길 — 홍천 한옥 펜션 강산재 예약 안내</title>",
     "<title>Information &amp; Directions — Gangsanjae, Hongcheon</title>"),
    ('<meta name="description" content="강산재 이용안내. 최대 12인 기준 요금과 바비큐 세트, 체크인 시간, 취소 규정과 오시는 길까지. 홍천 한옥 독채 강산재 예약 전 확인하세요.">',
     '<meta name="description" content="Rates, occupancy, check-in and check-out times, cancellation policy and directions to Gangsanjae in Hongcheon, Korea.">'),
    ('<meta property="og:title" content="이용안내 · 오시는 길 — 홍천 한옥 펜션 강산재">',
     '<meta property="og:title" content="Information — Gangsanjae">'),
    ('<meta property="og:description" content="요금과 이용 규정, 오시는 길 안내. 문의는 카카오톡으로 1시간 이내 응답합니다.">',
     '<meta property="og:description" content="Rates, occupancy, check-in and directions.">'),
    ("<h1>이용안내</h1>", "<h1>Information</h1>"),
    ("<p>예약 전 확인해 주세요</p>", "<p>Please read before booking</p>"),
    ("<h2>요금</h2>", "<h2>Rates</h2>"),
    ('<h3 style="color: var(--on-dark);">1박 요금</h3>', '<h3 style="color: var(--on-dark);">Per night</h3>'),
    ('<p class="when" style="color: #b6bfb6;">독채 전체 · 날짜에 따라 다름</p>',
     '<p class="when" style="color: #b6bfb6;">Whole house · varies by date</p>'),
    ("750,000원 ~ 950,000원", "KRW 750,000 – 950,000"),
    ("<h3>기준 인원</h3>\n      <p class=\"when\">추가 인원은 별도</p>",
     "<h3>Occupancy</h3>\n      <p class=\"when\">Extra guests charged separately</p>"),
    ('<p class="price" style="font-size: 24px;">기준 4인 · 최대 12인</p>',
     '<p class="price" style="font-size: 24px;">4 guests included · 12 max</p>'),
    ("<h3>입실 · 퇴실</h3>\n      <p class=\"when\">한옥 독채 1동 전체</p>",
     "<h3>Check-in · out</h3>\n      <p class=\"when\">The entire hanok, to yourselves</p>"),
    ('<p class="note" style="margin-top:24px;">※ 주중 · 주말 · 성수기 구간별 요금과 <span class="tbc">[인원 추가 요금 기준 확인 필요]</span></p>',
     '<p class="note" style="margin-top:24px;">Weekday, weekend and peak-season rates, and the charge for extra guests <span class="tbc">[to be confirmed]</span></p>'),
    ('<p class="note" style="margin-top:6px;">※ 네이버 예약(N페이) 및 에어비앤비로도 예약하실 수 있습니다 </p>',
     '<p class="note" style="margin-top:6px;">You can also book through Airbnb, or through Naver Booking if you have a Korean account.</p>'),
    ("<h2>이용 정보</h2>", "<h2>Details</h2>"),
    ("<div><dt>기준 인원</dt><dd>기준 4인 · 최대 12인 (8인 이상 사전 상담 후 예약)</dd></div>",
     "<div><dt>Occupancy</dt><dd>4 guests included · 12 maximum (parties over 8 by prior arrangement)</dd></div>"),
    ("<div><dt>구성</dt><dd>독채 1동 · 침실 5 · 침대 3 · 이불세트 6 · 욕실 2</dd></div>",
     "<div><dt>Layout</dt><dd>One private house · 5 bedrooms · 3 beds · 6 floor-bedding sets · 2 bathrooms</dd></div>"),
    ("<div><dt>주차</dt><dd>건물 부지 내 무료 주차</dd></div>",
     "<div><dt>Parking</dt><dd>Free, on site</dd></div>"),
    ("<div><dt>바비큐</dt><dd>웨버그릴 + 야자숯 세트 — 4~8인 기준 50,000원</dd></div>",
     "<div><dt>Barbecue</dt><dd>Weber grill and coconut charcoal set — KRW 50,000 for 4–8 guests</dd></div>"),
    ("<div><dt>입실 · 퇴실</dt><dd>입실 오후 3시 · 퇴실 오전 11시</dd></div>",
     "<div><dt>Check-in · out</dt><dd>From 3 pm · until 11 am</dd></div>"),
    ('<div><dt>조식</dt><dd class="tbc">[제공 여부 및 가격 확인 필요]</dd></div>',
     '<div><dt>Breakfast</dt><dd class="tbc">[availability and price to be confirmed]</dd></div>'),
    ('<div><dt>반려동물 동반</dt><dd class="tbc">[가능 여부 확인 필요]</dd></div>',
     '<div><dt>Pets</dt><dd class="tbc">[to be confirmed]</dd></div>'),
    ('<div><dt>흡연 · 파티</dt><dd class="tbc">[규정 확인 필요]</dd></div>',
     '<div><dt>Smoking · parties</dt><dd class="tbc">[policy to be confirmed]</dd></div>'),
    ("<div><dt>예약 채널</dt><dd>홈페이지 문의 · 네이버 예약 · 에어비앤비</dd></div>",
     "<div><dt>How to book</dt><dd>Enquire with us directly · Airbnb · Naver Booking</dd></div>"),
    ("<h2>취소 및 환불 규정</h2>", "<h2>Cancellation &amp; refunds</h2>"),
    ("[취소 · 환불 규정 확인 필요 — 이용일 기준 일자별 환불 비율 표로 구성]",
     "[Cancellation policy to be added — refund percentages by days before arrival]"),
    ("<h2>오시는 길</h2>", "<h2>Getting here</h2>"),
    ('aria-label="카카오맵에서 강산재 위치 크게 보기"', 'aria-label="Open Gangsanjae’s location in Kakao Map"'),
    ('<a class="btn btn-primary" href="https://map.kakao.com/link/to/856382843" target="_blank" rel="noopener noreferrer">카카오맵 길찾기</a>',
     '<a class="btn btn-primary" href="https://map.kakao.com/link/to/856382843" target="_blank" rel="noopener noreferrer">Directions (Kakao Map)</a>'),
    ('>네이버지도로 보기</a>', '>Open in Naver Map</a>'),
    ('>지도 크게 보기</a>', '>View larger map</a>'),
    ("<h3>주소</h3>\n      <p>강원특별자치도 홍천군 서면 고루개길 110</p>",
     "<h3>Address</h3>\n      <p>110 Gorugae-gil, Seo-myeon, Hongcheon-gun,<br>Gangwon State, Republic of Korea</p>"),
    ("<h3>자가용</h3>\n      <p>내비게이션에 <strong>‘고루개길 110’</strong> 또는 ‘강산재한옥호텔’을 입력하십시오.</p>",
     "<h3>By car</h3>\n      <p>About 90 minutes from Seoul. Enter <strong>‘고루개길 110’</strong> into a Korean navigation app, or use the Kakao Map link above.</p>"),
    ("<h3>문의</h3>\n      <p><a href=\"tel:01090277662\">010-9027-7662</a><br>카카오톡 ID : ksanj</p>",
     f"<h3>Contact</h3>\n      <p><a href=\"{TEL_HREF}\">{TEL_TEXT}</a><br>Instagram DM · KakaoTalk ID : ksanj</p>"),
    ('<h3 class="reveal" style="font-size:22px; letter-spacing:.04em; margin-bottom:24px;">주변 관광지</h3>',
     '<h3 class="reveal" style="font-size:22px; letter-spacing:.04em; margin-bottom:24px;">Nearby</h3>'),
    ("<h3>수타사 · 공작산 생태숲 · 산소길</h3>", "<h3>Sutasa Temple &amp; the Gongjaksan forest trail</h3>"),
    ('<p class="desc">계곡과 숲길, 천년 고찰이 하나로 이어져 있습니다. 덕치천을 따라 난 산소길은 오르막이 거의 없어, 걷는다기보다 산책에 가깝습니다.</p>',
     '<p class="desc">A stream, a forest path and a thousand-year-old temple, all on one route. The trail along the Deokchi stream is almost flat — a stroll rather than a hike.</p>'),
    ('<p class="who">부모님 · 연인 · 조용한 걸음</p>', '<p class="who">Grandparents · couples · a quiet walk</p>'),
    ("<h3>팔봉산 · 홍천강</h3>", "<h3>Palbongsan &amp; the Hongcheon River</h3>"),
    ('<p class="desc">여덟 개의 암봉이 홍천강을 병풍처럼 두르고 섰습니다. 홍천을 대표하는 풍경이라, 사진 한 장 남기려 찾는 분이 많습니다.</p>',
     '<p class="desc">Eight rock peaks standing over the river like a folding screen. It is the view Hongcheon is known for, and most people come for the photograph.</p>'),
    ('<p class="who">등산 · 캠핑 · 사진</p>', '<p class="who">Hiking · camping · photography</p>'),
    ("<h3>알파카월드</h3>", "<h3>Alpaca World</h3>"),
    ('<p class="desc">넓은 숲을 그대로 두고 만든 체험 목장입니다. 알파카에게 직접 먹이를 주며 걸을 수 있어, 아이들이 좀처럼 지루해하지 않습니다.</p>',
     '<p class="desc">A working farm laid out through standing forest. Children can feed the alpacas and walk alongside them, and rarely get bored.</p>'),
    ('<p class="who">아이 동반 가족 · 커플</p>', '<p class="who">Families with children · couples</p>'),
]

PAGE["info.html"] += [
    ("<h2>궁금한 점은 바로 물어보십시오</h2>", "<h2>Ask us anything</h2>"),
    ("<p>1시간 이내 응답 · 응답률 100%</p>", "<p>We reply within the hour · 100% response rate</p>"),
    ('<a href="https://open.kakao.com/" class="btn btn-gold">카카오톡으로 바로 문의하기</a>',
     f'<a href="{enquiry_href()}" class="btn btn-gold" target="_blank" rel="noopener">{enquiry_label()}</a>'),
]

# ---------------------------------------------------------------- 생성
def apply(text, pairs, where, optional_all=False):
    """pairs 의 원소는 (원문, 번역) 또는 (원문, 번역, True=없어도 됨).

    COMMON 은 페이지마다 있고 없고가 갈리므로 optional_all 로 부릅니다.
    누락은 마지막 한글 잔존 검사에서 걸립니다."""
    for pair in pairs:
        src, dst = pair[0], pair[1]
        optional = optional_all or (len(pair) > 2 and pair[2])
        if src == dst:
            continue
        n = text.count(src)
        if n == 0:
            if optional:
                continue
            raise SystemExit(f"[{where}] 치환 대상을 찾지 못했습니다:\n  {src[:110]}")
        # 헤더와 푸터에 같은 링크가 있으므로 전부 바꿉니다
        text = text.replace(src, dst)
    return text

def head_links(page):
    """canonical · og:url · hreflang 을 영문 기준으로 다시 씁니다."""
    slug = "" if page == "index.html" else "/" + page[:-5]
    return (
        f'<link rel="canonical" href="{SITE}/en{slug or ""}">\n'
        f'<meta property="og:url" content="{SITE}/en{slug or ""}">\n'
        f'<link rel="alternate" hreflang="ko" href="{SITE}{slug or "/"}">\n'
        f'<link rel="alternate" hreflang="en" href="{SITE}/en{slug or ""}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{SITE}{slug or "/"}">'
    )

def build(page):
    src = io.open(os.path.join(ROOT, page), encoding="utf-8").read()
    out = apply(src, COMMON, page, optional_all=True)
    out = apply(out, PAGE[page], page)
    for ko, en in ALT.items():
        out = out.replace(f'alt="{ko}"', f'alt="{en}"')

    slug = "" if page == "index.html" else "/" + page[:-5]
    out = out.replace('<html lang="ko">', '<html lang="en">', 1)
    out = out.replace('<meta property="og:locale" content="ko_KR">',
                      '<meta property="og:locale" content="en_US">')
    out = out.replace('<meta property="og:site_name" content="강산재 한옥호텔">',
                      '<meta property="og:site_name" content="Gangsanjae">')
    # canonical / og:url 을 hreflang 묶음으로 교체
    out = re.sub(r'<link rel="canonical" href="[^"]*">\n<meta property="og:url" content="[^"]*">',
                 head_links(page).replace("\\", "\\\\"), out, count=1)
    # 자산 경로는 루트 기준이라 그대로, 내부 링크만 /en 으로
    out = out.replace('href="/#booking"', 'href="/en#booking"')
    # 언어 전환기 — 실제 링크로
    out = out.replace('<span class="lang">KR / EN</span>',
                      f'<span class="lang"><a href="{slug or "/"}">KR</a> / <strong>EN</strong></span>')
    # JSON-LD (index 만 보유)
    out = out.replace('"name": "강산재",', '"name": "Gangsanjae",')
    out = out.replace('"alternateName": "자연숲속 한옥호텔 강산재",',
                      '"alternateName": "Gangsanjae Hanok Hotel",')
    out = out.replace('"description": "강원 홍천 4만 평 숲속의 전통 한옥 독채 숙소",',
                      '"description": "A private traditional hanok on 33 acres of forest in Hongcheon, Korea",')
    out = out.replace('"addressRegion": "강원특별자치도",', '"addressRegion": "Gangwon State",')
    out = out.replace('"addressLocality": "홍천군",', '"addressLocality": "Hongcheon-gun",')
    out = out.replace('"streetAddress": "서면 고루개길 110"',
                      '"streetAddress": "110 Gorugae-gil, Seo-myeon"')

    dst = os.path.join(ROOT, "en", page)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    io.open(dst, "w", encoding="utf-8").write(out)
    return dst, out

def main():
    made = []
    for page in PAGES:
        dst, out = build(page)
        # 남은 한글 검사 — 의도적으로 남긴 내비게이션 주소만 허용
        # HTML 주석은 유지보수용이라 한국어로 둡니다 — 검사에서 제외
        scan = re.sub(r"<!--.*?-->", "", out, flags=re.S)
        # 한국 내비게이션 앱에 그대로 입력해야 하는 주소는 남겨 둡니다
        for a in ["‘고루개길 110’"]:
            scan = scan.replace(a, "")
        leftover = re.findall(r"[가-힣][가-힣 ·]*", scan)
        if leftover:
            raise SystemExit(f"[{page}] 번역되지 않은 한글이 남았습니다: {leftover[:8]}")
        made.append(dst)
        print(f"  생성 {os.path.relpath(dst, ROOT)}")
    print(f"완료 — {len(made)}개 페이지")

if __name__ == "__main__":
    main()
