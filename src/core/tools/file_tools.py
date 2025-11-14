"""
File Tools Module

파일 관리 관련 도구들을 제공합니다.
OneDrive, 로컬 파일 시스템, 문서 생성 등
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
import logging
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)


class OneDriveTool:
    """OneDrive 파일 관리 도구"""

    def __init__(self):
        """Initialize OneDrive Tool"""
        # NOTE: 실제 환경에서는 Microsoft Graph API를 사용
        # 현재는 로컬 파일 시스템으로 시뮬레이션
        self.base_path = Path("./output/onedrive")
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info("OneDriveTool initialized (local simulation mode)")

    def upload_file(
        self,
        file_path: str,
        destination_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        파일 업로드

        Args:
            file_path: 업로드할 파일 경로
            destination_path: OneDrive 대상 경로
            overwrite: 덮어쓰기 여부

        Returns:
            Dict: 업로드 결과
        """
        try:
            source = Path(file_path)
            if not source.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Simulate OneDrive upload (local copy)
            dest = self.base_path / destination_path
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {destination_path}")

            # Copy file
            import shutil
            shutil.copy2(source, dest)

            logger.info(f"File uploaded: {destination_path}")

            return {
                "success": True,
                "path": str(dest),
                "size": dest.stat().st_size,
                "modified_at": datetime.fromtimestamp(dest.stat().st_mtime).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        폴더 생성

        Args:
            folder_path: 생성할 폴더 경로

        Returns:
            Dict: 생성 결과
        """
        try:
            folder = self.base_path / folder_path
            folder.mkdir(parents=True, exist_ok=True)

            logger.info(f"Folder created: {folder_path}")

            return {
                "success": True,
                "path": str(folder)
            }

        except Exception as e:
            logger.error(f"Failed to create folder: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_files(self, folder_path: str = "") -> Dict[str, Any]:
        """
        파일 목록 조회

        Args:
            folder_path: 조회할 폴더 경로

        Returns:
            Dict: 파일 목록
        """
        try:
            folder = self.base_path / folder_path
            if not folder.exists():
                return {
                    "success": True,
                    "files": []
                }

            files = []
            for item in folder.iterdir():
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.base_path)),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })

            logger.info(f"Listed {len(files)} items in {folder_path}")

            return {
                "success": True,
                "files": files
            }

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class DocumentGeneratorTool:
    """문서 생성 도구"""

    def __init__(self):
        """Initialize Document Generator Tool"""
        self.output_dir = Path("./output/documents")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("DocumentGeneratorTool initialized")

    def generate_markdown(
        self,
        title: str,
        content: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Markdown 문서 생성

        Args:
            title: 문서 제목
            content: 문서 내용
            filename: 파일명 (선택적)

        Returns:
            Dict: 생성 결과
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{title.replace(' ', '_')}_{timestamp}.md"

            file_path = self.output_dir / filename

            # Generate markdown content
            markdown = f"# {title}\n\n"
            markdown += f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            markdown += "---\n\n"
            markdown += content

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

            logger.info(f"Markdown document generated: {filename}")

            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "size": file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Failed to generate markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_json(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        JSON 문서 생성

        Args:
            data: JSON 데이터
            filename: 파일명 (선택적)

        Returns:
            Dict: 생성 결과
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data_{timestamp}.json"

            file_path = self.output_dir / filename

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"JSON document generated: {filename}")

            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "size": file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Failed to generate JSON: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_report(
        self,
        report_type: str,
        title: str,
        sections: Dict[str, str],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        보고서 생성

        Args:
            report_type: 보고서 타입 (weekly, meeting, status)
            title: 보고서 제목
            sections: 섹션별 내용 {"섹션명": "내용"}
            filename: 파일명 (선택적)

        Returns:
            Dict: 생성 결과
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d")
                filename = f"{report_type}_report_{timestamp}.md"

            file_path = self.output_dir / filename

            # Generate report content
            report = f"# {title}\n\n"
            report += f"**보고서 유형**: {report_type}\n"
            report += f"**작성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report += "---\n\n"

            # Add sections
            for section_name, section_content in sections.items():
                report += f"## {section_name}\n\n"
                report += f"{section_content}\n\n"

            # Add footer
            report += "---\n\n"
            report += "*본 보고서는 AI Agent에 의해 자동 생성되었습니다.*\n"

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"Report generated: {filename}")

            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "size": file_path.stat().st_size,
                "report_type": report_type
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def append_to_file(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        파일에 내용 추가

        Args:
            file_path: 파일 경로
            content: 추가할 내용

        Returns:
            Dict: 실행 결과
        """
        try:
            path = Path(file_path)

            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Content appended to: {file_path}")

            return {
                "success": True,
                "file_path": str(path),
                "new_size": path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Failed to append to file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instances
_onedrive_tool_instance = None
_document_generator_instance = None


def get_onedrive_tool() -> OneDriveTool:
    """OneDriveTool 싱글톤 인스턴스 반환"""
    global _onedrive_tool_instance
    if _onedrive_tool_instance is None:
        _onedrive_tool_instance = OneDriveTool()
    return _onedrive_tool_instance


def get_document_generator() -> DocumentGeneratorTool:
    """DocumentGeneratorTool 싱글톤 인스턴스 반환"""
    global _document_generator_instance
    if _document_generator_instance is None:
        _document_generator_instance = DocumentGeneratorTool()
    return _document_generator_instance


if __name__ == "__main__":
    # Test the tools
    logging.basicConfig(level=logging.INFO)

    # Test OneDrive Tool
    print("\n=== Testing OneDrive Tool ===")
    onedrive = OneDriveTool()

    # Create folder
    result = onedrive.create_folder("reports/2024")
    print(f"Create folder: {result}")

    # Test Document Generator
    print("\n=== Testing Document Generator ===")
    doc_gen = DocumentGeneratorTool()

    # Generate markdown
    result = doc_gen.generate_markdown(
        title="Test Document",
        content="This is a test document."
    )
    print(f"Generate markdown: {result}")

    # Generate report
    result = doc_gen.generate_report(
        report_type="weekly",
        title="주간 업무 보고서",
        sections={
            "주요 성과": "- 작업 1 완료\n- 작업 2 진행 중",
            "이슈사항": "특이사항 없음",
            "다음 주 계획": "- 작업 3 시작\n- 작업 2 완료"
        }
    )
    print(f"Generate report: {result}")
