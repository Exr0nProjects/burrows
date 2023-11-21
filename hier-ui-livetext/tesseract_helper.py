import pytesseract
from dataclasses import dataclass
from typing import List
import pandas as pd

confidence_thresh = 0.1

@dataclass
class TessaractWord:
    left: int
    top: int
    width: int
    height: int
    text: str
    confidence: float

def get_flattened_words(image) -> List[TessaractWord]:
    ocr_data: pd.DataFrame = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
    for i, (level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text) in ocr_data.iterrows():
        if level == 5 and conf > confidence_thresh:
            yield TessaractWord(left, top, width, height, text, conf)
