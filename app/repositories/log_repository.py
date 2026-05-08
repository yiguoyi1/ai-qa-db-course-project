import oracledb


class LogRepository:
    def create_login_log(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        ip_address: str | None,
        result: str,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO login_log (
                user_id,
                ip_address,
                result
            ) VALUES (
                :user_id,
                :ip_address,
                :result
            )
            """,
            {
                "user_id": user_id,
                "ip_address": ip_address,
                "result": result,
            },
        )

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

    def create_operation_log(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        op_type: str,
        op_content: str,
    ) -> None:
        safe_content = op_content[:200]
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO operation_log (
                user_id,
                op_type,
                op_content
            ) VALUES (
                :user_id,
                :op_type,
                :op_content
            )
            """,
            {
                "user_id": user_id,
                "op_type": op_type,
                "op_content": safe_content,
            },
        )
