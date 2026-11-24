import base64
import os
from io import BytesIO
from typing import Union, List
import fitz
import io
import requests
from PIL import Image
import pymupdf
from loguru import logger

class ImageProcessor:
    """Utility class for image processing tasks."""

    @staticmethod
    def get_image_info_from_url(url: str) -> tuple[bytes, str]:
        """
        Lấy nội dung (bytes) và mime_type của ảnh từ URL.
        Sử dụng phương thức HEAD để lấy mime_type trước cho hiệu quả.
        """
        try:
            # Gửi yêu cầu HEAD để lấy header mà không tải toàn bộ file
            head_response = requests.head(url, allow_redirects=True, timeout=5)
            head_response.raise_for_status()  # Báo lỗi nếu request không thành công (vd: 404)

            content_type = head_response.headers.get('Content-Type')

            # Kiểm tra xem content_type có phải là của một hình ảnh không
            if content_type and content_type.startswith('image/'):
                # Nếu đúng là ảnh, giờ mới tải toàn bộ nội dung
                image_response = requests.get(url, allow_redirects=True, timeout=10)
                image_response.raise_for_status()
                image_bytes = image_response.content
                return image_bytes, content_type
            else:
                logger.error(f"URL không trỏ đến một ảnh hợp lệ. Content-Type: {content_type}")
                return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi truy cập URL: {e}")
            return None, None
            
    @staticmethod
    def load_image(image_input: str | Image.Image) -> Image.Image:
        """Load image from file path, URL, or return if already a PIL Image."""
        if isinstance(image_input, Image.Image):
            return image_input
        elif isinstance(image_input, str):
            if image_input.startswith("http://") or image_input.startswith("https://"):
                response = requests.get(image_input)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            elif os.path.exists(image_input):
                return Image.open(image_input)
            else:
                raise ValueError(f"Invalid image path or URL: {image_input}")
        else:
            raise ValueError("Image input must be a file path, URL, or PIL Image.")

    @staticmethod
    def encode_from_file_path(file_path: str):
        """Encode image from local file path"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Image file not found: {file_path}")

            with Image.open(file_path) as img:
                # Get image format
                image_format = img.format.lower() if img.format else "png"

                # Convert to RGB if necessary
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                image_size = img.size
                # Save to bytes
                img_byte_arr = BytesIO()
                save_format = "PNG" if image_format == "png" else "JPEG"
                img.save(img_byte_arr, format=save_format)
                image_bytes = img_byte_arr.getvalue()

            # Encode to base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Determine MIME type
            mime_type = "image/png" if image_format == "png" else "image/jpeg"

            data_url = f"data:{mime_type};base64,{base64_image}"
            logger.info(f"Successfully encoded image from file: {file_path}")
            return data_url, image_size

        except Exception as e:
            logger.error(f"Failed to encode image from file {file_path}: {e}")
            raise e

    @staticmethod
    def encode_from_image_url(image_url: str):
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            if not image_bytes:
                raise ValueError("No image data received from URL")

            if image_bytes.startswith(b"<!DOCTYPE") or image_bytes.startswith(b"<html"):
                raise ValueError("Received HTML content instead of image data")

            try:
                with Image.open(BytesIO(image_bytes)) as img:
                    image_format = img.format.lower() if img.format else "jpeg"

                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGB")

                    img_byte_arr = BytesIO()
                    save_format = "JPEG" if image_format in ["jpg", "jpeg"] else image_format.upper()
                    img.save(img_byte_arr, format=save_format)
                    processed_image_bytes = img_byte_arr.getvalue()
                    image_size = img.size

            except Exception as img_error:
                raise ValueError(f"Invalid image format: {img_error}")

            base64_image = base64.b64encode(processed_image_bytes).decode("utf-8")

            mime_type = f"image/{image_format}"
            if image_format in ["jpg", "jpeg"]:
                mime_type = "image/jpeg"
            elif image_format == "png":
                mime_type = "image/png"
            elif image_format == "webp":
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"

            data_url = f"data:{mime_type};base64,{base64_image}"
            logger.info(f"Successfully encoded image from {image_url} as {mime_type}")
            return data_url, image_size

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch image from URL {image_url}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to encode image from URL {image_url}: {e}")
            raise e

    @staticmethod
    def encode_from_pil_image(image: Image.Image):
        try:
            # Validate PIL image
            if image is None:
                raise ValueError("Image is None")

            # Check image size
            if image.size[0] <= 0 or image.size[1] <= 0:
                raise ValueError(f"Invalid image size: {image.size}")

            # Basic validation - check if we can access image pixels
            try:
                # Try to access image data to check if it's valid
                if hasattr(image, "load"):
                    try:
                        image.load()  # Load image data
                    except Exception as load_error:
                        logger.warning(f"Image load failed: {load_error}")
                        # Continue anyway, save might still work
            except Exception as access_error:
                logger.warning(f"Image access check failed: {access_error}")
                # Continue anyway, save might still work

            # Convert mode if necessary
            try:
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")
            except Exception as convert_error:
                logger.error(f"Failed to convert image mode: {convert_error}")
                raise ValueError(f"Image mode conversion failed: {convert_error}")

            image_size = image.size
            img_byte_arr = BytesIO()

            # Try PNG first (more reliable), fallback to JPEG
            save_format = "PNG"
            mime_type = "image/png"

            try:
                image.save(img_byte_arr, format=save_format)
            except Exception as save_error:
                logger.warning(f"Failed to save as PNG: {save_error}, trying JPEG")
                try:
                    # Reset BytesIO for retry
                    img_byte_arr = BytesIO()
                    save_format = "JPEG"
                    mime_type = "image/jpeg"
                    image.save(img_byte_arr, format=save_format)
                except Exception as jpeg_error:
                    logger.error(f"Failed to save as JPEG: {jpeg_error}")
                    raise ValueError(f"Image save failed for both PNG and JPEG: PNG({save_error}), JPEG({jpeg_error})")

            image_bytes = img_byte_arr.getvalue()

            # Verify we got data
            if not image_bytes or len(image_bytes) == 0:
                raise ValueError("No image data generated")

            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            data_url = f"data:{mime_type};base64,{base64_image}"
            logger.info(f"Successfully encoded PIL image as {mime_type}, size: {image_size}")
            return data_url, image_size

        except Exception as e:
            logger.error(f"Failed to encode PIL image: {e}")
            raise e

    @staticmethod
    def encode(image_input: str | Image.Image):
        """Process image input which can be a file path, URL, or PIL Image."""
        if isinstance(image_input, str):
            if image_input.startswith("http://") or image_input.startswith("https://"):
                return ImageProcessor.encode_from_image_url(image_input)
            else:
                return ImageProcessor.encode_from_file_path(image_input)
        elif isinstance(image_input, Image.Image):
            return ImageProcessor.encode_from_pil_image(image_input)
        else:
            raise ValueError("Invalid image input type. Must be file path, URL, or PIL Image.")
        
    @staticmethod
    def resize(image: Image.Image | str, target_size: tuple[int, int]) -> Image.Image:
        """Resize image to target size while maintaining aspect ratio."""
        if not isinstance(image, Image.Image) and not isinstance(image, str):
            raise ValueError("Input must be a PIL Image or a string")
            
        if isinstance(image, str):
            image = ImageProcessor.load_image(image)

        original_size = image.size
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        logger.info(f"Resized image from {original_size} to {image.size}")
        return image

def convert_pdf_to_pil(
    pdf_source: Union[str, bytes], 
    dpi: int = 200, 
    include_annots: bool = True
) -> List[Image.Image]:
    """
    Chuyển đổi file PDF (từ đường dẫn, URL hoặc bytes) thành một danh sách ảnh PIL.
    Hàm này được tối ưu dựa trên tài liệu PyMuPDF mới nhất.

    Args:
        pdf_source (Union[str, bytes]): 
            - Một chuỗi (str) có thể là đường dẫn file trên máy hoặc một URL.
            - Một đối tượng bytes chứa nội dung file PDF.
        dpi (int, optional): 
            Độ phân giải (dots per inch) cho ảnh đầu ra. Giá trị cao hơn cho chất lượng tốt hơn.
            Defaults to 200.
        include_annots (bool, optional): 
            Có render các chú thích (annotations) lên ảnh hay không.
            Defaults to True.

    Returns:
        List[Image.Image]: Một danh sách các đối tượng ảnh PIL, mỗi đối tượng là một trang.
                           Trả về danh sách rỗng nếu có lỗi.
    """
    pil_images = []
    pdf_document = None
    
    try:
        # --- Bước 1: Mở file PDF từ nguồn cung cấp ---
        if isinstance(pdf_source, str):
            if pdf_source.startswith(('http://', 'https://')):
                # Xử lý URL
                print(f"Đang tải PDF từ URL: {pdf_source}")
                response = requests.get(pdf_source, timeout=30)
                response.raise_for_status()
                pdf_bytes = response.content
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            else:
                # Xử lý đường dẫn file
                pdf_document = fitz.open(pdf_source)
        elif isinstance(pdf_source, bytes):
            # Xử lý đối tượng bytes
            pdf_document = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            raise TypeError("pdf_source phải là str (path/URL) hoặc bytes.")

        # --- Bước 2: Lặp qua các trang và chuyển đổi ---
        for page in pdf_document:  # Lặp trực tiếp qua doc như trong tài liệu
            # Sử dụng tham số 'dpi' trực tiếp, đây là cách làm được khuyên dùng
            # và đơn giản hơn việc tạo Matrix.
            # Thêm tham số 'annots' để kiểm soát việc render chú thích.
            pix = page.get_pixmap(dpi=dpi, annots=include_annots)
            
            # Chuyển pixmap (định dạng của PyMuPDF) sang ảnh PIL
            img_data = pix.tobytes("png")  # Chuyển sang bytes định dạng PNG
            pil_image = Image.open(io.BytesIO(img_data))
            pil_images.append(pil_image)
            
        return pil_images

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return []
    finally:
        # Đảm bảo file PDF luôn được đóng
        if pdf_document:
            pdf_document.close()

def convert_images_to_pdf(images: list[str] | list[Image.Image], output_path: str = "output.pdf"):
    """
    Convert images to PDF.
    """
    try:
        doc = pymupdf.open()
        for i, f in enumerate(images):
            if isinstance(f, str):
                if f.startswith("http://") or f.startswith("https://"):
                    r = requests.get(f, allow_redirects=True, timeout=30)
                    data = r.content
                    img = pymupdf.Document(stream=data)  # open pic as document
                    rect = img[0].rect  # pic dimension
                    pdfbytes = img.convert_to_pdf()  # make a PDF stream
                    img.close()  # no longer needed
                    imgPDF = pymupdf.open("pdf", pdfbytes)  # open stream as PDF
                    page = doc.new_page(width = rect.width,  # new page with ...
                                    height = rect.height)  # pic dimension
                    page.show_pdf_page(rect, imgPDF, 0)  # image fills the page

        doc.save(output_path)
        logger.info(f"Successfully converted images to PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting images to PDF: {e}")
        return None