from services.list_course.service import ListeCourses
from services.ocr.ocr_processor import PaddleOCRProcessor

serviceListeCourse = ListeCourses()

# Singleton OCR
ocr_processor = PaddleOCRProcessor()

from services.ocr.structuration import StructurationLLM
structuration_processor = StructurationLLM()

# from services.list_course.service import ListeCourses
# ListeCourses_processor = ListeCourses()