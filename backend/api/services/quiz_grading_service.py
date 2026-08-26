from quiz_generation.quiz_generator import grade_short_answer


def grade_submission(quiz_data: dict, mcq_answers: dict, short_answers: dict):
    """
    quiz_data: the saved quiz.json content -> {"quiz": [{"mcqs": [...], "short_answers": [...]}, ...]}
    mcq_answers: {question_text: chosen_option_letter}
    short_answers: {question_text: student_answer_text}

    Returns: (score, total_questions, detailed_results, weak_areas)
    """
    detailed_results = []
    weak_areas = []
    correct_count = 0
    total_questions = 0

    for section in quiz_data["quiz"]:
        for q in section["mcqs"]:
            total_questions += 1
            student_choice = mcq_answers.get(q["question"])
            is_correct = student_choice == q["correct_option"]
            if is_correct:
                correct_count += 1
            else:
                weak_areas.append({
                    "question": q["question"],
                    "your_answer": student_choice,
                    "correct_answer": q["correct_option"],
                    "timestamp": q["timestamp"],
                    "explanation": q.get("explanation", ""),
                })
            detailed_results.append({
                "type": "mcq",
                "question": q["question"],
                "your_answer": student_choice,
                "correct_answer": q["correct_option"],
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
            })

        for q in section["short_answers"]:
            total_questions += 1
            student_answer = short_answers.get(q["question"], "")
            grade_result = grade_short_answer(q["question"], q["model_answer"], student_answer)
            is_correct = grade_result.get("correct", False)
            if is_correct:
                correct_count += 1
            else:
                weak_areas.append({
                    "question": q["question"],
                    "your_answer": student_answer,
                    "correct_answer": q["model_answer"],
                    "timestamp": q["timestamp"],
                    "explanation": grade_result.get("feedback", ""),
                })
            detailed_results.append({
                "type": "short_answer",
                "question": q["question"],
                "your_answer": student_answer,
                "model_answer": q["model_answer"],
                "is_correct": is_correct,
                "feedback": grade_result.get("feedback", ""),
            })

    return correct_count, total_questions, detailed_results, weak_areas