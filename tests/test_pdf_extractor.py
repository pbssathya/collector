import pymupdf

from collector.extractors.pdf import extract_pdf_structure, iter_pdf_lines


def test_pdf_extractor_preserves_page_line_and_span_structure():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "KARUNYA LOTTERY NO.KR-765th DRAW")
    page.insert_text((72, 90), "held on:- 22/08/2026,3:00 PM")
    content = document.tobytes()
    document.close()

    structure = extract_pdf_structure(content)
    lines = list(iter_pdf_lines(structure))

    assert len(structure["pages"]) == 1
    assert [line["text"] for line in lines] == [
        "KARUNYA LOTTERY NO.KR-765th DRAW",
        "held on:- 22/08/2026,3:00 PM",
    ]
    assert lines[0]["page"] == 1
    assert lines[0]["bbox"] is not None
    assert lines[0]["spans"][0]["text"] == "KARUNYA LOTTERY NO.KR-765th DRAW"
