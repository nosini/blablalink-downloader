# blablalink extractor for gallery-dl

An external [gallery-dl](https://github.com/mikf/gallery-dl) extractor for
[blablalink.com](https://www.blablalink.com/), the NIKKE community site. It
uses the site's public JSON API, so no login is needed, and downloads the
original uploads (the CDN URLs without the `?height=…&width=…` size query).

## Supported URLs

| URL | Result |
| --- | --- |
| `https://www.blablalink.com/post/detail?post_uuid=ID` | one post |
| `https://www.blablalink.com/user?openid=OPENID` | all posts of a user |
| `https://www.blablalink.com/?plate_id=N` | feed of a board (plate)¹ |
| `https://www.blablalink.com/` | the home feed |

¹ The site doesn't put the board in its URLs; `?plate_id=N` is a convention of
this extractor. Board ids come from the API (`GetPlateList`), e.g. 38.

Posts without images (video links, text-only) are skipped; set
`extractor.blablalink.empty` to `true` to still emit their metadata.

Output goes to `blablalink/{user[username]} ({user[intl_openid]})/` as
`{post_uuid}_{num}.{ext}`. Post fields such as `title`, `tags`, `date` and
`user` are available to `-K`, `--filter` and format strings.

## Using it

gallery-dl loads every `.py` file in a directory given with `-X`, so keep this
file in a directory of its own:

```sh
gallery-dl -X /path/to/blablalink-downloader 'https://www.blablalink.com/user?openid=…'
```

Or set it permanently in `config.json`:

```json
{"extractor": {"module-sources": ["~/.config/gallery-dl/extractors"]}}
```

### With the gallery-dl Flatpak

The Flatpak already has read/write access to `~/.config/gallery-dl`, so no
repository change is needed:

```sh
mkdir -p ~/.config/gallery-dl/extractors
cp blablalink.py ~/.config/gallery-dl/extractors/
```

then add the `module-sources` setting above to `~/.config/gallery-dl/config.json`
and run as usual, with a download folder granted:

```sh
flatpak run --filesystem=xdg-download:rw eu.nosini.GalleryDl \
  -d "$(xdg-user-dir DOWNLOAD)" 'https://www.blablalink.com/post/detail?post_uuid=…'
```

(Not yet run inside the Flatpak itself; the agent container can't run
Flatpaks. It was tested with gallery-dl 1.33.0-dev on Python 3.11.)

To ship it inside the package instead, it would have to become a
`gallery_dl/extractor/blablalink.py` module registered in the extractor
`modules` list, which means patching upstream on every update; the
config-directory route avoids that.
