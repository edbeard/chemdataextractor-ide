# -*- coding: utf-8 -*-
"""
Elsevier XML reader

.. codeauthor:: Callum Court <cc889@cam.ac.uk>


Readers for Elsevier XML files.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import six
from ..scrape.clean import clean, Cleaner
from ..doc.table import Cell, Table
from ..doc.text import Caption, Title, Heading, Citation
from ..doc.document import Document
from ..doc.figure import Figure
from ..doc.meta import MetaData
from ..errors import ReaderError
from .markup import XmlReader
from lxml import etree
from collections import defaultdict

import re

# XML stripper that removes the tags around numbers in chemical formulas
strip_els_xml = Cleaner(strip_xpath='.//ce:inf | .//ce:italic | .//ce:bold | .//ce:formula | .//mml:* | .//ce:sup',
                        kill_xpath='.//ce:cross-ref//ce:sup | .//ce:table//ce:sup | .//ce:cross-ref | .//ce:cross-refs')


def fix_elsevier_xml_whitespace(document):
    """ Fix tricky xml tags"""
    # space hsp  and refs correctly
    for el in document.xpath('.//ce:hsp'):
        parent = el.getparent()
        previous = el.getprevious()
        if parent is None:
            continue
        # Append the text to previous tail (or parent text if no previous), ensuring newline if block level
        if el.text and isinstance(el.tag, six.string_types):
            if previous is None:
                if parent.text:
                    if parent.text.endswith(' '):
                        parent.text = (parent.text or '') + '' + el.text
                    else:
                        parent.text = (parent.text or '') + ' ' + el.text
            else:
                if previous.tail:
                    if previous.tail.endswith(' '):
                        previous.tail = (previous.tail or '') + '' + el.text
                    else:
                        previous.tail = (previous.tail or '') + ' ' + el.text
        # Append the tail to last child tail, or previous tail, or parent text, ensuring newline if block level
        if el.tail:
            if len(el):
                last = el[-1]
                last.tail = (last.tail or '') + el.tail
            elif previous is None:
                if el.tail.startswith(' '):
                    parent.text = (parent.text or '') + '' + el.tail
                else:
                    parent.text = (parent.text or '') + ' ' + el.tail
            else:
                if el.tail.startswith(' '):
                    previous.tail = (previous.tail or '') + '' + el.tail
                else:
                    previous.tail = (previous.tail or '') + ' ' + el.tail

        index = parent.index(el)
        parent[index:index + 1] = el[:]
    return document


def els_xml_whitespace(document):
    """ Remove whitespace in xml.text or xml.tails for all elements, if it is only whitespace """
    # selects all tags and checks if the text or tail are spaces
    for el in document.xpath('//*'):
        if str(el.text).isspace():
            el.text = ''
        if str(el.tail).isspace():
            el.tail = ''
    # debug, check the document
    # print(etree.tostring(document, pretty_print=True))
    # sys.exit()
    return document


class ElsevierXmlReader(XmlReader):
    """Reader for Elsevier XML documents."""

    cleaners = [clean, fix_elsevier_xml_whitespace, els_xml_whitespace, strip_els_xml]

    etree.FunctionNamespace("http://www.elsevier.com/xml/svapi/article/dtd").prefix = 'default'
    etree.FunctionNamespace("http://www.elsevier.com/xml/bk/dtd").prefix = 'bk'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/cals/dtd").prefix = 'cals'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/dtd").prefix = 'ce'
    etree.FunctionNamespace("http://www.elsevier.com/xml/ja/dtd").prefix = 'ja'
    etree.FunctionNamespace("http://www.w3.org/1998/Math/MathML").prefix = 'mml'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/struct-aff/dtd").prefix = 'sa'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/struct-bib/dtd").prefix = 'sb'
    etree.FunctionNamespace("http://www.elsevier.com/xml/common/table/dtd").prefix = 'tb'
    etree.FunctionNamespace("http://www.w3.org/1999/xlink").prefix = 'xlink'
    etree.FunctionNamespace("http://www.elsevier.com/xml/xocs/dtd").prefix = 'xocs'
    etree.FunctionNamespace("http://purl.org/dc/elements/1.1/").prefix = 'dc'
    etree.FunctionNamespace("http://purl.org/dc/terms/").prefix = 'dcterms'
    etree.FunctionNamespace("http://prismstandard.org/namespaces/basic/2.0/").prefix = 'prism'
    etree.FunctionNamespace("http://www.w3.org/2001/XMLSchema-instance").prefix = 'xsi'

    root_css = 'default|full-text-retrieval-response'
    title_css = 'dc|title'
    heading_css = 'ce|section-title'
    table_css = 'ce|table'
    table_caption_css = 'ce|table ce|caption'
    table_head_row_css = 'cals|thead cals|row'
    table_body_row_css = 'cals|tbody cals|row'
    table_cell_css = 'ce|entry'
    table_footnote_css = 'table-wrap-foot p'
    figure_css = 'ce|figure'
    figure_caption_css = 'ce|figure ce|caption'
    # figure_label_css = 'ce|figure ce|label'
    figure_link_css = 'ce|figure ce|link'
    # figure_css = 'dl[class~=figure]'
    # figure_img_css = 'img[src]'
    # figure_caption_css = ' .caption'
    reference_css = 'ce|cross-ref, ce|cross-refs'
    citation_css = 'ce|bib-reference'

    metadata_css = 'xocs|meta'
    metadata_title_css = 'xocs|normalized-article-title'
    metadata_author_css = 'xocs|normalized-first-auth-surname'
    metadata_journal_css = 'xocs|srctitle'
    metadata_volume_css = 'xocs|vol-first, xocs|volume-list xocs|volume'
    metadata_issue_css = 'xocs|issns xocs|issn-primary-formatted'
    metadata_publisher_css = 'xocs|copyright-line'
    metadata_date_css = 'xocs|available-online-date, xocs|orig-load-date'
    metadata_firstpage_css = 'xocs|first-fp'
    metadata_lastpage_css = 'xocs|last-lp'
    metadata_doi_css = 'xocs|doi, xocs|eii'
    metadata_pii_css = 'xocs|pii-unformatted'

    ignore_css = 'ce|bibliography, ce|acknowledgment, ce|correspondence, ce|author, ce|doi, ja|jid, ja|aid, ce|pii, xocs|oa-sponsor-type, xocs|open-access, default|openaccess,' \
                 'default|openaccessArticle, dc|format, dc|creator, dc|identifier,' \
                 'default|eid, default|pii, xocs|meta, xocs|ref-info, default|scopus-eid,' \
                 'xocs|normalized-srctitle,' \
                 'xocs|eid, xocs|hub-eid, xocs|normalized-first-auth-surname,' \
                 'xocs|normalized-first-auth-initial, xocs|refkeys,' \
                 'xocs|attachment-eid, xocs|attachment-type,' \
                 'ja|jid, ce|given-name, ce|surname, ce|affiliation, ce|cross-refs, ce|cross-ref,' \
                 'ce|grant-sponsor, ce|grant-number, prism|copyright,' \
                 'xocs|pii-unformatted, xocs|ucs-locator, ce|copyright,' \
                 'prism|publisher, prism|*, xocs|copyright-line, xocs|cp-notice,' \
                 'dc|description'

    url_prefix = 'https://sciencedirect.com/science/article/pii/'

    def detect(self, fstring, fname=None):
        """Elsevier document detection based on string found in xml"""
        if fname and not fname.endswith('.xml'):
            return False
        if b'xmlns="http://www.elsevier.com/xml/svapi/article/dtd"' in fstring:
            return True
        return False

    def _parse_metadata(self, el, refs, specials):
        title = self._css(self.metadata_title_css, el)
        authors = self._css(self.metadata_author_css, el)
        publisher = self._css(self.metadata_publisher_css, el)
        journal = self._css(self.metadata_journal_css, el)
        date = self._css(self.metadata_date_css, el)
        language = self._css(self.metadata_language_css, el)
        volume = self._css(self.metadata_volume_css, el)
        issue = self._css(self.metadata_issue_css, el)
        firstpage = self._css(self.metadata_firstpage_css, el)
        lastpage = self._css(self.metadata_lastpage_css, el)
        doi = self._css(self.metadata_doi_css, el)
        pii = self._css(self.metadata_pii_css, el)
        pdf_url = self._css(self.metadata_pdf_url_css, el)
        html_url = self._css(self.metadata_html_url_css, el)

        metadata = {
            '_title': title[0].text if title else None,
            '_authors': [i.text for i in authors] if authors else None,
            '_publisher': publisher[0].text if publisher else None,
            '_journal': journal[0].text if journal else None,
            '_date': date[0].text if date else None,
            '_language': language[0].text if language else None,
            '_volume': volume[0].text if volume else None,
            '_issue': issue[0].text if issue else None,
            '_firstpage': firstpage[0].text if firstpage else None,
            '_lastpage': lastpage[0].text if lastpage else None,
            '_doi': doi[0].text if doi else None,
            '_pdf_url': self.url_prefix + pdf_url[0].text if pdf_url else None,
            '_html_url': self.url_prefix + html_url[0].text if html_url else self.url_prefix + pii[0].text
        }
        meta = MetaData(metadata)
        return [meta]

    def _parse_table_rows(self, els, refs, specials):
        hdict = {}
        for row, tr in enumerate(els):
            colnum = 0
            for td in self._css(self.table_cell_css, tr):
                cell = self._parse_text(td, refs=refs, specials=specials, element_cls=Cell)
                namest = int([i for i in td.get('namest', '1').split('col') if i][0])
                nameend = int([i for i in td.get('nameend', '1').split('col') if i][0])
                colspan = (nameend - namest) + 1
                rowspan = int(td.get('morerows', '0')) + 1
                for i in range(colspan):
                    for j in range(rowspan):
                        rownum = row + j
                        if not rownum in hdict:
                            hdict[rownum] = {}
                        while colnum in hdict[rownum]:
                            colnum += 1
                        hdict[rownum][colnum] = cell[0]
                    colnum += 1
        rows = []
        for row in sorted(hdict):
            rows.append([])
            for col in sorted(hdict[row]):
                rows[-1].append(hdict[row][col])
        for r in rows:
            r.extend([Cell('')] * (len(max(rows, key=len)) - len(r)))
        rows = [r for r in rows if any(r)]
        return rows

    def _parse_figure(self, el, root, refs, specials):

        # Getting attachements (which contain the images)
        img_filetypes_css = 'xocs|attachment xocs|filename'
        filenames = self._css(img_filetypes_css, root)

        caps = self._css(self.figure_caption_css, el)
        caption = self._parse_text(caps[0], refs=refs, specials=specials, element_cls=Caption)[0] if caps else Caption('')
        link = self._css(self.figure_link_css, el)
        img_id = link[0].attrib['locator'] if link else ''
        if img_id is not None:

            # Get the filename of the image
            filename_candidates = [filename for filename in filenames if img_id in filename.text and '_lrg' in filename.text]
            filename = filename_candidates[0] if filename_candidates else ''

            pii = link[0].attrib['{http://www.w3.org/1999/xlink}href'].split('/')[0][4:]
            #img_url = 'https://api.elsevier.com/content/object/pii/' + pii + '/ref/' + img_id + '/high'
            img_url = 'https://ars.els-cdn.com/content/image/1-s2.0-' + pii + '-' + filename.text
        fig = Figure(caption, url=img_url, id=img_id)
        return [fig]

    def parse(self, fstring):
        root = self._make_tree(fstring)
        if root is None:
            raise ReaderError
        root = self._css(self.root_css, root)[0]
        print(etree.tostring(root, pretty_print=True))
        for cleaner in self.cleaners:
            cleaner(root)
        specials = {}
        refs = defaultdict(list)
        titles = self._css(self.title_css, root)
        headings = self._css(self.heading_css, root)
        figures = self._css(self.figure_css, root)
        tables = self._find_table(root)
        citations = self._css(self.citation_css, root)
        references = self._css(self.reference_css, root)
        ignores = self._css(self.ignore_css, root)
        for reference in references:
            refs[reference.getparent()].extend(self._parse_reference(reference))
        for ignore in ignores:
            specials[ignore] = []
        for title in titles:
            specials[title] = self._parse_text(title, element_cls=Title, refs=refs, specials=specials)
        for heading in headings:
            specials[heading] = self._parse_text(heading, element_cls=Heading, refs=refs, specials=specials)
        for figure in figures:
            specials[figure] = self._parse_figure(figure, root, refs=refs, specials=specials)
        for table in tables:
            tab_id = table[0] if type(table) == tuple else table
            specials[tab_id] = self._parse_table(table, refs=refs, specials=specials)
        for citation in citations:
            specials[citation] = self._parse_text(citation, element_cls=Citation, refs=refs, specials=specials)
        elements = self._parse_element(root, specials=specials, refs=refs)
        return Document(*elements)