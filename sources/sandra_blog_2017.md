---
name: sandra-blog-2017
description: Sandra Rothbard's "Wall to Wall – Summer 2017" travel blog — what it covers, how to get into it, and the full 70-entry index. Read before researching anything about her China route.
type: reference
---
Aaron's friend Sandra Rothbard blogged her summer 2017 Israel → Hong Kong → China → Cambodia trip at https://walltowall2017.wordpress.com/ — 70 entries, 10 May to 25 July 2017. All 70 were read in full on 2026-09-09; the distilled content lives in [[sandra-china-tips]] and the 2026-specific crossover in [[sandra-2026-crossover]].

**The blog is PRIVATE.** WebFetch, curl and the WordPress public API all fail. She locked it partway through the trip (post "Blog to become private", 26 June 2017) and approved followers only.

How to get back in (verified 2026-09-09)
- It can only be read from a browser already logged into a WordPress.com account she has approved. Aaron's Chrome has that session; the Claude desktop browser pane does not.
- Use Claude in Chrome. If `list_connected_browsers` returns empty, the extension isn't reachable — Chrome must be running with the extension enabled and signed into the same claude.ai account.
- There is no sitemap.xml (404). Enumerate by fetching `/`, `/page/2/` … `/page/8/` from inside the page and collecting hrefs matching `/YYYY/MM/DD/slug/`. Eight archive pages yield exactly 70 unique posts.
- Pull each post with same-origin `fetch(url, {credentials:'include'})` and take `.entry-content`. Full corpus is ~220,000 characters.
- `javascript_tool` truncates its return value at roughly 1,000 characters, so do NOT try to return post text from it. Instead write the text into the page (`document.body` → a `<pre>`) in ~45,000-character slices and read each slice with `get_page_text`, which caps at 50,000. Five slices covers everything.

Notes on the blog itself
- Publish dates are not trip dates. She wrote offline and batch-uploaded when wifi allowed, so a dozen posts share a publish date and the archive order is scrambled. The date in each post *title* is the real one. She apologizes for this repeatedly, along with spelling (broken keyboard, no spell check).
- Photos are central to the posts and are not captured by a text pull. She also deliberately held back most transportation and freight photos for a freight website she was building afterward.
- Aaron appears throughout as Sandra's partner: he traveled Israel with her (Jerusalem old city tour, Dead Sea, Akko, kibbutz Magal), was her "porter" for the flight out, recommended the Angkor National Museum, the Angkor guidebook and Haven restaurant in Siem Reap, and they spoke by phone from Chengdu.
- She is an urban planner (NYU Wagner), which shapes the whole blog — freight, ports, transit, museums, planning agencies. She audited Prof. Zhan Guo's NYU Shanghai summer planning course for the tours only.

Route and dates
- Israel 10–28 May: Tel Aviv, Yaffo, Haifa, Akko, Jerusalem, Dead Sea, kibbutz Magal
- Hong Kong 30 May – 8 June (+ Macau day trip 6 June)
- Guangzhou 8–13 June
- Siem Reap, Cambodia 13–16 June
- Yunnan 16–26 June: Kunming, Dali, Lijiang, Tiger Leaping Gorge, Shangri-La
- Chengdu 26–29 June; Yichang / Three Gorges Dam 29 June – 1 July
- Shanghai 1–14 July (audited the NYU course; day trip to Suzhou)
- Xi'an 15–19 July
- Beijing 19–25 July, home 25 July

## Full entry index (70 posts, by trip date)

| Trip date | Title | Chars |
|---|---|---|
| 2017-05-10 | So long New York, hello world! | 408 |
| ~2017-05-20 | Tel Aviv | 159 |
| ~2017-05-21 | Yaffo | 191 |
| ~2017-05-21 | Haifa | 828 |
| 2017-05-22 | 5/22/17 Akko | 435 |
| 2017-05-23 | 5/23/17 Tuesday Tel Aviv Again | 644 |
| 2017-05-24 | 5/24/17 Taglit Baby | 228 |
| 2017-05-25 | 5/25/17 Jerusalem | 832 |
| 2017-05-26 | 5/26/17 Friday Dead Sea | 707 |
| 2017-05-27 | 5/27/17 Shabbat in Magal | 1226 |
| 2017-05-28 | 5/28/17 Sunday Bye Bye | 193 |
| 2017-05-29 | 5/29/17 Monday day of travel | 2666 |
| 2017-05-30 | 5/30/17 Tuesday Hong Kong! | 1636 |
| 2017-05-31 | 5/31/17 Hong Kong solo | 2421 |
| 2017-06-01 | 6/1/17 Thursday | 2624 |
| 2017-06-02 | 6/2/17 Friday | 1870 |
| 2017-06-03 | 6/3/17 Saturday | 1018 |
| 2017-06-04 | 6/4/17 Sunday Beach Day | 736 |
| 2017-06-05 | 6/5/17 Monday Big Buddha | 1432 |
| 2017-06-06 | 6/6/17 Tuesday Macau | 2825 |
| 2017-06-07 | 6/7/17 Wednesday | 2433 |
| 2017-06-08 | 6/8/17 Goodbye Hong Kong, Hello China! | 3886 |
| 2017-06-09 | 6/9/17 Friday Guangzhou | 3089 |
| 2017-06-10 | 6/10/17 Saturday Guangzhou | 3448 |
| 2017-06-10 | Poor wifi = difficulty uploading photos = delay in blog posts | 195 |
| 2017-06-11 | 6/11/17 Sunday Guangzhou | 3564 |
| 2017-06-12 | 6/12/17 Monday Guangzhou | 1522 |
| 2017-06-13 | 6/13/17 Tuesday To Guangzhou, Thanks for Everything! Sandra Rothbard | 3672 |
| 2017-06-14 | 6/14/17 Wednesday Siem Reap | 4953 |
| 2017-06-15 | 6/15/17 Thursday Siem Reap | 2636 |
| 2017-06-16 | 6/16/17 Siem Reap/Kunming | 2006 |
| 2017-06-17 | 6/17/17 Kunming | 2637 |
| 2017-06-18 | 6/18/17 Kunming to Dali | 5637 |
| 2017-06-19 | 6/19/17 Dali | 4455 |
| 2017-06-20 | 6/20/17 Dali | 3330 |
| 2017-06-21 | 6/21/17 From Dali to Lijiang | 2944 |
| 2017-06-22 | 6/22/17 Lijiang | 2765 |
| 2017-06-23 | 6/23/17 To Tiger Leaping Gorge! | 5329 |
| 2017-06-24 | 6/24/17 Second Day of Hike | 6152 |
| 2017-06-25 | 6/25/17 Shangri La | 4738 |
| 2017-06-26 | Blog to become private | 243 |
| 2017-06-26 | 6/26/17 Shangri La to Chengdu | 7560 |
| 2017-06-27 | 6/27/17 Chengdu | 5324 |
| 2017-06-28 | 6/28/17 Chengdu | 7931 |
| 2017-06-29 | 6/29/17 Chengdu to Yichang | 7728 |
| 2017-06-30 | 6/30/17 Dam Day | 3824 |
| 2017-07-01 | 7/1/17 Off to Shanghai | 6768 |
| 2017-07-02 | 7/2/17 Good Morning Shanghai! | 3146 |
| 2017-07-03 | 7/3/17 NYU Shanghai | 8100 |
| 2017-07-04 | 7/4/17 Shanghai Slept In | 2651 |
| 2017-07-05 | 7/5/17 School Day | 2815 |
| 2017-07-06 | 7/6/17 | 2430 |
| 2017-07-07 | 7/7/17 | 3632 |
| 2017-07-08 | 7/8/17 No Class Today | 3837 |
| 2017-07-09 | 7/9/17 Suzhou | 4721 |
| 2017-07-10 | 7/10/17 Design Day | 4964 |
| 2017-07-11 | 7/11/17 transport day | 3116 |
| 2017-07-12 | 7/12/17 Steel Day | 3546 |
| 2017-07-13 | 7/13/17 Oy Shanghai | 5533 |
| 2017-07-14 | 7/14/17 Port Day | 5640 |
| 2017-07-15 | 7/15/17 Xi'an | 1386 |
| 2017-07-16 | 7/16/17 Xi'an City Wall | 2314 |
| 2017-07-17 | 7/17/17 It finally happened… | 1313 |
| 2017-07-18 | 7/18/17 Terra-cotta Warriors | 2490 |
| 2017-07-19 | 7/19/17 Off to Beijing! | 1072 |
| 2017-07-20 | 7/20/17 Major Beijing Sites | 3041 |
| 2017-07-21 | 7/21/17 Feeling Better and Better Weather! | 3428 |
| 2017-07-22 | 7/22/17 More Heat | 1673 |
| 2017-07-23 | 7/23/17 The Great Wall of China | 3770 |
| 2017-07-25 | 7/24/17-7/25/17 I'm coming home!!! | 3800 |
