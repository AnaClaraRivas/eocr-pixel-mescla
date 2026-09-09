import os
import time

import fitz  # PyMuPDF
from PIL import ExifTags, Image

from core.analysis_result import AnalysisResult
from core.evidence import Evidence


class MetadataAnalyzer:
    """Extrai metadados e gera indícios explicáveis para revisão humana."""

    EDITING_SOFTWARE = ("photoshop", "gimp", "canva")

    def analyze(self, file_path):
        start = time.time()

        try:
            extension = os.path.splitext(file_path)[1].lower()

            if extension == ".pdf":
                data, evidences = self._analyze_pdf(file_path)
            elif extension in (".jpg", ".jpeg", ".png"):
                data, evidences = self._analyze_image(file_path)
            else:
                return AnalysisResult(
                    success=False,
                    module="metadata",
                    warnings=["Formato de arquivo não suportado."],
                )

            return AnalysisResult(
                success=True,
                module="metadata",
                score=sum(evidence.weight for evidence in evidences),
                data=data,
                evidences=evidences,
                execution_time=time.time() - start,
            )
        except Exception as error:
            return AnalysisResult(
                success=False,
                module="metadata",
                warnings=[str(error)],
                execution_time=time.time() - start,
            )

    def _editing_software_evidence(self, software):
        software_normalized = str(software or "").lower()

        for name in self.EDITING_SOFTWARE:
            if name in software_normalized:
                return Evidence(
                    code="EDITING_SOFTWARE",
                    message=(
                        f"Os metadados mencionam o software {name}. Isso indica "
                        "processamento ou edição, mas não comprova adulteração."
                    ),
                    severity="low",
                    weight=5,
                )

        return None

    def _analyze_pdf(self, file_path):
        with fitz.open(file_path) as pdf:
            metadata = pdf.metadata or {}
            creator = metadata.get("creator", "")
            producer = metadata.get("producer", "")
            evidence = self._editing_software_evidence(f"{creator} {producer}")

            data = {
                "type": "PDF",
                "pages": len(pdf),
                "author": metadata.get("author"),
                "creator": creator,
                "producer": producer,
                "creation_date": metadata.get("creationDate"),
                "modification_date": metadata.get("modDate"),
                "encrypted": pdf.is_encrypted,
            }

        return data, [evidence] if evidence else []

    def _analyze_image(self, file_path):
        with Image.open(file_path) as image:
            exif_data = {
                ExifTags.TAGS.get(tag_id, tag_id): value
                for tag_id, value in image.getexif().items()
            }

            evidences = []
            software = exif_data.get("Software", "")
            editing_evidence = self._editing_software_evidence(software)

            if editing_evidence:
                evidences.append(editing_evidence)

            if not exif_data:
                evidences.append(
                    Evidence(
                        code="NO_EXIF",
                        message=(
                            "Imagem sem metadados EXIF. Isso é comum em arquivos "
                            "baixados, reenviados ou exportados e não indica fraude sozinho."
                        ),
                        severity="low",
                        weight=0,
                    )
                )

            data = {
                "type": "IMAGE",
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "exif": exif_data,
                "software": software or None,
            }

        return data, evidences

