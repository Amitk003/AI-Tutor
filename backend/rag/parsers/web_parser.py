"""
Web HTML and URL Document Parser.
Fetches web content or parses HTML DOM strings preserving headings and paragraphs.
"""

from typing import List
import httpx
from loguru import logger

from backend.rag.parsers.base import BaseDocumentParser
from backend.rag.schemas import ElementType, ExtractedElement
from backend.utils.helpers import sanitize_text


class WebDocumentParser(BaseDocumentParser):
    """Web URL and HTML document parser."""

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in (".html", ".htm", "url")

    async def parse(self, target_url: str) -> List[ExtractedElement]:
        logger.info("Fetching and parsing web page URL: url={url}", url=target_url)
        elements: List[ExtractedElement] = []

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(target_url)
                response.raise_for_status()
                html_text = response.text

            # Parse HTML content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_text, "html.parser")

            # Remove scripts, styles, navs
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            heading_path: List[str] = []

            for elem in soup.find_all(["h1", "h2", "h3", "p", "table"]):
                text = sanitize_text(elem.get_text())
                if not text:
                    continue

                if elem.name == "h1":
                    element_type = ElementType.HEADING_1
                    heading_path = [text]
                elif elem.name == "h2":
                    element_type = ElementType.HEADING_2
                    heading_path = [heading_path[0], text] if heading_path else [text]
                elif elem.name == "h3":
                    element_type = ElementType.HEADING_3
                    heading_path.append(text)
                else:
                    element_type = ElementType.PARAGRAPH

                elements.append(
                    ExtractedElement(
                        element_type=element_type,
                        content=text,
                        page_number=1,
                        heading_path=list(heading_path),
                        metadata={"url": target_url, "tag": elem.name},
                    )
                )

            logger.info("Web parsing complete: url={url} elements={count}", url=target_url, count=len(elements))
            return elements
        except Exception as e:
            logger.error("Failed to parse web URL: url={url} error={err}", url=target_url, err=str(e))
            raise
