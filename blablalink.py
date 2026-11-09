# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extractors for https://www.blablalink.com/

External gallery-dl extractor module. Load it with
`extractor.module-sources` or `--source`; see README.md.
"""

from gallery_dl.extractor.common import Extractor, Message
from gallery_dl import exception, text

BASE_PATTERN = r"(?:https?://)?(?:www\.)?blablalink\.com"


class BlablalinkExtractor(Extractor):
    """Base class for blablalink extractors"""
    category = "blablalink"
    root = "https://www.blablalink.com"
    directory_fmt = ("{category}", "{user[username]} ({user[intl_openid]})")
    filename_fmt = "{post_uuid}_{num:>02}.{extension}"
    archive_fmt = "{post_uuid}_{filename}"
    request_interval = (0.5, 1.5)
    api_root = ("https://api.blablalink.com"
                "/api/ugc/direct/standalonesite/Dynamics")

    def items(self):
        for post in self.posts():
            if self._skip(post):
                continue
            files = self._extract_files(post)
            post["count"] = len(files)
            post["date"] = self.parse_timestamp(post["created_on"])
            post["date_updated"] = self.parse_timestamp(post["modified_on"])

            yield Message.Directory, "", post
            for post["num"], url in enumerate(files, 1):
                text.nameext_from_url(url, post)
                yield Message.Url, url, post

    def posts(self):
        return ()

    def _skip(self, post):
        # video posts only carry an external link, no images
        return not post.get("pic_urls") and not self.config("empty", False)

    def _extract_files(self, post):
        # The size in the query is only layout metadata; without it the
        # CDN serves the original upload.
        return [url.partition("?")[0] for url in post["pic_urls"] if url]

    def _call(self, endpoint, **params):
        url = f"{self.api_root}/{endpoint}"
        data = self.request_json(
            url, method="POST", json=params,
            headers={"X-Language": "en"})
        if data.get("code"):
            raise exception.AbortExtraction(
                f"API error {data['code']}: {data.get('msg')}")
        return data["data"]

    def _pagination(self, endpoint, **params):
        params["limit"] = 20
        params["nextPageCursor"] = ""
        while True:
            data = self._call(endpoint, **params)
            yield from data["list"]

            info = data["page_info"]
            if info["is_finish"] or not data["list"]:
                return
            params["nextPageCursor"] = info["next_page_cursor"]


class BlablalinkPostExtractor(BlablalinkExtractor):
    """Extractor for single blablalink posts"""
    subcategory = "post"
    pattern = (BASE_PATTERN +
               r"/post/detail(?:/preview)?/?\?(?:.*&)?post_uuid=(\d+)")
    example = "https://www.blablalink.com/post/detail?post_uuid=1234567890"

    def posts(self):
        return (self._call("GetPost", post_uuid=self.groups[0]),)


class BlablalinkUserExtractor(BlablalinkExtractor):
    """Extractor for all posts of a blablalink user"""
    subcategory = "user"
    pattern = BASE_PATTERN + r"/user/?\?(?:.*&)?openid=([\w-]+)"
    example = "https://www.blablalink.com/user?openid=12345-1234567890"

    def posts(self):
        return self._pagination("GetUserPostList", intl_openid=self.groups[0])


class BlablalinkPlateExtractor(BlablalinkExtractor):
    """Extractor for the post feed of a blablalink plate (board)

    This URL form is a convention of this extractor, the website itself
    does not put the board in its URLs.
    """
    subcategory = "plate"
    pattern = BASE_PATTERN + r"/?\?(?:.*&)?plate_id=(\d+)"
    example = "https://www.blablalink.com/?plate_id=38"

    def posts(self):
        return self._pagination(
            "GetPostListNew", plate_id=int(self.groups[0]))


class BlablalinkFeedExtractor(BlablalinkExtractor):
    """Extractor for the blablalink home feed"""
    subcategory = "feed"
    pattern = BASE_PATTERN + r"/?$"
    example = "https://www.blablalink.com/"

    def posts(self):
        return self._pagination("GetPostListNew")
