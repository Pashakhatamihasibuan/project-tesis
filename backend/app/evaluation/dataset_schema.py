"""
Schema dan validator untuk dataset evaluasi (150 pasang pertanyaan +
ground truth, sesuai Bab III.C.5 Prosedur Pengembangan).

PENTING -- ini BUKAN dataset final penelitian kamu. File
`data/eval_dataset_template.json` di sebelah modul ini hanya berisi
5 contoh entri untuk menunjukkan FORMAT yang benar. Dataset 150
pertanyaan yang sesungguhnya harus disusun berdasarkan dokumen resmi
UNY yang sebenarnya dan divalidasi oleh minimal dua pakar (dosen/ahli
bidang terkait) sesuai desain penelitian -- proses ini TIDAK BISA
diotomatisasi/dibuatkan, karena validitasnya bergantung pada
pengetahuan domain manusia yang menguasai peraturan akademik UNY.
"""
import json
from dataclasses import dataclass
from enum import Enum


class QuestionType(str, Enum):
    FAKTUAL = "faktual"
    PROSEDURAL = "prosedural"
    INFERENSIAL = "inferensial"


@dataclass
class EvalQuestion:
    id: str
    question: str
    ground_truth: str
    question_type: QuestionType
    source_document: str
    source_page: int | None = None
    validated_by: list[str] | None = None  # nama/inisial pakar yang memvalidasi


class DatasetValidationError(Exception):
    pass


def load_dataset(path: str) -> list[EvalQuestion]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    questions = []
    for i, item in enumerate(raw):
        required = {"id", "question", "ground_truth", "question_type", "source_document"}
        missing = required - set(item.keys())
        if missing:
            raise DatasetValidationError(f"Entri ke-{i} kekurangan field: {missing}")

        try:
            qtype = QuestionType(item["question_type"])
        except ValueError:
            raise DatasetValidationError(
                f"Entri '{item['id']}': question_type '{item['question_type']}' tidak valid. "
                f"Harus salah satu dari: {[e.value for e in QuestionType]}"
            )

        questions.append(
            EvalQuestion(
                id=item["id"],
                question=item["question"],
                ground_truth=item["ground_truth"],
                question_type=qtype,
                source_document=item["source_document"],
                source_page=item.get("source_page"),
                validated_by=item.get("validated_by"),
            )
        )
    return questions


def validate_dataset_composition(questions: list[EvalQuestion], expected_total: int = 150) -> dict:
    """
    Cek komposisi dataset sesuai desain penelitian: total 150 soal,
    tervalidasi minimal 2 pakar, tercakup 3 jenis pertanyaan.
    Dipanggil SEBELUM menjalankan evaluasi RAGAS -- gagal cepat kalau
    dataset belum siap, daripada ketahuan di tengah proses evaluasi
    yang berjam-jam.
    """
    issues = []

    if len(questions) != expected_total:
        issues.append(
            f"Jumlah soal {len(questions)}, seharusnya {expected_total} sesuai Bab III.D.3."
        )

    type_counts = {t: 0 for t in QuestionType}
    unvalidated = []
    for q in questions:
        type_counts[q.question_type] += 1
        if not q.validated_by or len(q.validated_by) < 2:
            unvalidated.append(q.id)

    if unvalidated:
        issues.append(
            f"{len(unvalidated)} soal belum divalidasi minimal 2 pakar: "
            f"{unvalidated[:5]}{'...' if len(unvalidated) > 5 else ''}"
        )

    for qtype, count in type_counts.items():
        if count == 0:
            issues.append(f"Tidak ada soal bertipe '{qtype.value}' -- desain penelitian mensyaratkan ketiga jenis.")

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "total_questions": len(questions),
        "type_distribution": {t.value: c for t, c in type_counts.items()},
    }
