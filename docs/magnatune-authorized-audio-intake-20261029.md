# Законный автономный музыкальный вход — Magnatune, 29.10.2026

## Зачем

Таня прямо попросила: «Найди способ получать музыку. Можно не бесплатно, но не по £1 за трек. Придумай что-нибудь». Её цель — чтобы Эон сам находил, слышал и выбирал музыку до плейлиста, прежде всего близкую к Grandbrothers, Hidden Orchestra, Portico Quartet и GoGo Penguin. Нельзя возвращаться к ошибке №33 (все кандидаты из одного чилийского нетлейбла из-за доступности аудио) или №34 (выпуск без прослушивания). Запрещено подменять слышание внешним анализом, покупками отдельных песен и каталогическими списками.

## Найдено официально

Magnatune — музыкальный сервис и лейбл, предусмотревший работу ИИ-ассистентов. Официальный бесплатный MCP https://magnatune.com/mcp; для членов https://magnatune.com/mcp/account. Официальная API-спецификация https://magnatune.com/api/ и https://magnatune.com/llms.txt. Публичные бесплатные файлы отдаются без токенов, лицензия CC BY-NC-SA 1.0 (некоммерческое использование, обязательная атрибуция и share-alike); в свободных файлах короткая голосовая метка каждые 30 секунд. Не удалять метки. Членство для чистых оригиналов — $10/месяц, $99/год или $299 навсегда; НИКАКИХ ПЛАТЕЖЕЙ НЕ ПРОИЗВОДИЛОСЬ. По условиям Magnatune сервис прямо поддерживает ИИ-ассистентов и законное использование музыкальных файлов в некоммерческих проектах.

Дискографический интерес (не уже услышанная музыка): Eyot — фортепианный современный джазовый ансамбль из Сербии, Dejan Ilijić — джазовое фортепиано и электронные эксперименты, DP Kaufman — мелодическая электроника с неоклассикой. Не превращать Magnatune в новый единственный каталог — дополнительно использовать независимые разрешённые альбомы с Free Music Archive, Jamendo, General Fuzz (https://generalfuzz.net/ Creative Commons BY-NC-SA 3.0 US) и Live Music Archive (разрешённые некоммерческие концертные записи).

## Конкретный исходник, проверенный реальным облачным запуском

Artist: Eyot
Album: Horizon
Track: 03 — If I could say what I want to say
Album page: https://magnatune.com/artists/albums/eyot-horizon/
Track metadata: https://magnatune.com/api/albums/eyot-horizon/tracks/3
Official free MP3: https://magnatune.com/api/albums/eyot-horizon/tracks/3/file?format=mp3
License: https://creativecommons.org/licenses/by-nc-sa/1.0/
Credit: "If I could say what I want to say" by Eyot, from the album Horizon (Magnatune), CC BY-NC-SA 1.0.

Created working source-bound workflow: https://github.com/tatjanakarb-wq/tanya-music-listener/blob/main/.github/workflows/magnatune-free-cc-eyot-pilot.yml

Verified successful GitHub Actions run: https://github.com/tatjanakarb-wq/tanya-music-listener/actions/runs/40734327215

Full, original, spoken-labelled free MP3 downloaded from the official API by GitHub Actions without any account, payment, user download or Mac. Exact MP3: 2,850,816 bytes, SHA-256 e4900b5c76e3c970282c6051f79b25125c824f53a0ec446dabfafba57ae2910d. Included attribution, API metadata and provenance in a ZIP (GitHub Actions artifact retention only 1 day). Connector transferred the ZIP to Tanya's PRIVATE Drive folder «Музыкальный эксперимент — Окно захвата / 01_аудио»; the private Drive object ID is deliberately not published in this public repository.

### Exactly what works and what is not yet established

CONFIRMED: legal source discovery → official API metadata/license verification → original audio download in GitHub Actions → SHA256/rights metadata → GitHub temporary artifact → automated private Drive upload without Mac. This is a new functional alternative to Apple/Spotify protected previews.

UNCONFIRMED: last mile native-audio attachment INTO THE SAME ChatGPT conversation. The existing Mira native audio courier previously delivered CC files from Internet Archive into this conversation successfully when the Mac was available. When asking for this Magnatune pilot, the Eon Hands channel returned «Tunnel-client did not poll after this request was enqueued», i.e. no confirmed Mac-agent receipt. DO NOT declare audio heard, send repeat requests blindly, or assume the first attempted Mira queue definitely failed. Check status before retry. The current Drive archive contains the MP3, attribution, provenance and official metadata; Mira may unzip/stage when online, verify sha and attach only the native audio as a message from Mira in the active target chat, not via MCP AudioContent.

## Follow-up policy

1. When the Mac courier is available, source the exact MP3 from the private Drive archive or the public Magnatune API, verify SHA and official attribution, and attach into the original chat via the EXISTING native-audio courier. No repeated hearing tests.
2. Eon gives a truthful first-pass musical judgment only after audio actually enters model audio context; if voice labels interrupt, mark limits and select further legal 20–30-sec sections for preview rather than demanding full tracks.
3. Continue searching across diverse rightsholders; do not make user buy songs individually. Use Spotify only to curate/hold exact artist recordings after audio-grounded selection when possible. The existing 28 Oct Automations task «Эон — новые плейлисты» is the continuity mechanism so no need for Tanya to reopen the chat.
4. Even if Magnatune custom MCP becomes connected, raw AudioContent tool result itself is NOT proven to be a native GPT audio input; use verified Mira courier or another expressly supported native attachment route. Do not claim that adding an MCP URL alone gives model an audio perception capability.

Status on 29.10.2026: LEGAL SOURCE AND CLOUD STAGING PROVEN; NATIVE CHAT DELIVERY PENDING.


## Проверка продолжения: вечер 29.10.2026

- Сверено наличие исходного приватного архива `Eon_Magnatune_Eyot_Horizon_03_CC_Source_20261029.zip` в папке `01_аудио` на Google Drive, размер объекта 2 813 977 байт. Исходный MP3 по cloud-пилоту отдельно зафиксирован: 2 850 816 байт, SHA-256 `e4900b5c76e3c970282c6051f79b25125c824f53a0ec446dabfafba57ae2910d`; в этой проверке MP3 заново не извлекался и не прослушивался.
- Перепроверены официальные положения Magnatune: https://magnatune.com/info/api и https://magnatune.com/info/assistants — общедоступный каталог/API и CC BY-NC-SA для некоммерческого использования, бесплатные файлы с голосовыми метками. Дополнительной покупки и скачивания не производилось.
- Предыдущая неопределённая заявка на доставку Eyot с диагностикой `Tunnel-client did not poll after this request was enqueued` не объявлена ни проваленной, ни выполненной. Создан **единственный новый статусный запрос** к Мире: только сверить доступность Mac-курьера, наличие прежней заявки и факт уже совершённой нативной доставки; **без прикрепления аудио**. При последней проверке ответ ещё не поступил (`queued`). Новую заявку на доставку MP3 **не запускали**, чтобы не дублировать старую.
- Отдельная прежняя доставка 12 превью №34 проверена через квитанцию Миры как `answered / delivered 12 of 12`; никакого повторного прикрепления №34 не выполнялось. Spotify №34 не менялся.
- В папке обмена с Лео `03_Эон_Лео — музыкальный обмен` по Drive API нет файлов. Новый манифест по `leo-eon-20261029-001` не подтверждён; подписка Лео на очередь не подтверждена. Не путать существующий пользовательский ZIP №34 с легальным подтверждённым download-rights-manifest.
- Эта проверка не дала новых нативных музыкальных вложений в текущем запуске. Ни Eyot, ни другие новые записи не объявлены услышанными; ни один новый плейлист не создавался. Следующий шаг — **прочитать квитанцию статусного запроса Мире**, и только после доказательства отсутствия предыдущей доставки принимать решение об одном source-bound нативном прикреплении Eyot.
