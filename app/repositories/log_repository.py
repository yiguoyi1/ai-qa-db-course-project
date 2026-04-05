import oracledb


class LogRepository:
    def create_prompt_log(
        self,
        connection: oracledb.Connection,
        question_id: int,
        prompt_text: str,
        response_text: str,
        token_usage: int,
        model_name: str,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO ai_prompt_log (
                question_id,
                prompt_text,
                response_text,
                token_usage,
                model_name
            ) VALUES (
                :question_id,
                :prompt_text,
                :response_text,
                :token_usage,
                :model_name
            )
            """,
            {
                "question_id": question_id,
                "prompt_text": prompt_text,
                "response_text": response_text,
                "token_usage": token_usage,
                "model_name": model_name,
            },
        )
