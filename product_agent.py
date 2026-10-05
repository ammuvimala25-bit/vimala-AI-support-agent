import os
import glob
import json
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KB_FOLDER = "knowledge_base"
COMPANY_FOLDER = "company_documents"
TICKET_FILE = "tickets.json"


class CustomerSupportAgent:

    def __init__(self):

        self.documents = []
        self.sources = []

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english"
        )

        self.matrix = None

        self.load_knowledge_base()

    # =====================================================
    # LOAD KNOWLEDGE
    # =====================================================

    def load_knowledge_base(self):

        self.documents = []
        self.sources = []

        folders = [
            KB_FOLDER,
            COMPANY_FOLDER
        ]

        for folder in folders:

            os.makedirs(folder, exist_ok=True)

            files = sorted(
                glob.glob(
                    os.path.join(folder, "*.txt")
                )
            )

            for file_path in files:

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8"
                    ) as file:

                        content = file.read().strip()

                    if content:

                        self.documents.append(content)

                        self.sources.append(
                            os.path.basename(file_path)
                        )

                except Exception as error:

                    print(
                        f"Could not read {file_path}: {error}"
                    )

        self.rebuild_index()

    # =====================================================
    # REBUILD INDEX
    # =====================================================

    def rebuild_index(self):

        if not self.documents:

            self.matrix = None
            return

        try:

            self.matrix = (
                self.vectorizer.fit_transform(
                    self.documents
                )
            )

        except Exception as error:

            print(
                f"Index error: {error}"
            )

            self.matrix = None

    # =====================================================
    # ADD DOCUMENTS
    # =====================================================

    def add_documents(
        self,
        documents,
        source_prefix="Online"
    ):

        for document in documents:

            if not document.strip():
                continue

            self.documents.append(
                document
            )

            self.sources.append(
                source_prefix
            )

        self.rebuild_index()

    # =====================================================
    # PRODUCT DOCUMENTS
    # =====================================================

    def add_product_documents(
        self,
        documents,
        product_name
    ):

        product_documents = []

        for document in documents:

            if not document.strip():
                continue

            product_document = (
                f"PRODUCT: {product_name}\n\n"
                f"{document}"
            )

            product_documents.append(
                product_document
            )

        self.add_documents(
            product_documents,
            f"Online Product - {product_name}"
        )

    # =====================================================
    # TNPSC DOCUMENTS
    # =====================================================

    def add_tnpsc_documents(
        self,
        documents,
        topic
    ):

        tnpsc_documents = []

        for document in documents:

            if not document.strip():
                continue

            tnpsc_documents.append(
                f"TNPSC TOPIC: {topic}\n\n"
                f"{document}"
            )

        self.add_documents(
            tnpsc_documents,
            f"TNPSC Online - {topic}"
        )

    # =====================================================
    # SEARCH
    # =====================================================

    def search(
        self,
        query,
        top_k=5
    ):

        if (
            self.matrix is None
            or not self.documents
        ):

            return []

        try:

            query_vector = (
                self.vectorizer.transform(
                    [query]
                )
            )

            scores = cosine_similarity(
                query_vector,
                self.matrix
            )[0]

            indexes = np.argsort(
                scores
            )[::-1]

            results = []

            for index in indexes[:top_k]:

                score = float(
                    scores[index]
                )

                if score <= 0:
                    continue

                results.append({
                    "text": self.documents[index],
                    "source": self.sources[index],
                    "score": score
                })

            return results

        except Exception as error:

            print(
                f"Search error: {error}"
            )

            return []

    # =====================================================
    # HUMAN ESCALATION
    # =====================================================

    def needs_human(
        self,
        query
    ):

        keywords = [
            "human",
            "agent",
            "person",
            "representative",
            "manager",
            "customer care",
            "customer service",
            "speak to someone",
            "talk to someone",
            "complaint",
            "supervisor"
        ]

        query_lower = query.lower()

        return any(
            keyword in query_lower
            for keyword in keywords
        )

    # =====================================================
    # ANSWER
    # =====================================================

    def answer(
        self,
        query,
        product_name=""
    ):

        results = self.search(
            query,
            top_k=5
        )

        if not results:

            return {
                "answer": (
                    "I could not find reliable information "
                    "in my knowledge base. "
                    "Please create a support ticket."
                ),
                "results": []
            }

        best_score = results[0]["score"]

        if best_score < 0.08:

            return {
                "answer": (
                    "I don't have enough reliable information "
                    "to answer this question. "
                    "Please create a support ticket."
                ),
                "results": results
            }

        answer = self.make_answer(
            query,
            results,
            product_name
        )

        return {
            "answer": answer,
            "results": results
        }

    # =====================================================
    # ANSWER GENERATOR
    # =====================================================

    def make_answer(
        self,
        query,
        results,
        product_name=""
    ):

        query_words = [
            word.lower()
            for word in query.split()
            if len(word) > 3
        ]

        selected_lines = []

        for result in results:

            lines = [
                line.strip()
                for line in result["text"].splitlines()
                if line.strip()
            ]

            for line in lines:

                line_lower = line.lower()

                if any(
                    word in line_lower
                    for word in query_words
                ):

                    if line not in selected_lines:

                        selected_lines.append(
                            line
                        )

        if not selected_lines:

            for result in results[:2]:

                lines = [
                    line.strip()
                    for line in result["text"].splitlines()
                    if line.strip()
                ]

                for line in lines[:2]:

                    if line not in selected_lines:

                        selected_lines.append(
                            line
                        )

        selected_lines = selected_lines[:4]

        answer = " ".join(
            selected_lines
        )

        if product_name:

            answer = (
                f"For {product_name}: "
                f"{answer}"
            )

        return answer[:900]

    # =====================================================
    # CREATE TICKET
    # =====================================================

    def create_ticket(
        self,
        customer_name,
        issue,
        product=""
    ):

        if os.path.exists(
            TICKET_FILE
        ):

            try:

                with open(
                    TICKET_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    tickets = json.load(file)

            except Exception:

                tickets = []

        else:

            tickets = []

        ticket_number = (
            len(tickets) + 1
        )

        ticket_id = (
            f"TKT-"
            f"{datetime.now().strftime('%Y%m%d')}-"
            f"{ticket_number:04d}"
        )

        ticket = {
            "ticket_id": ticket_id,
            "customer_name": customer_name,
            "product": product,
            "issue": issue,
            "status": "Open",
            "created_at": datetime.now().isoformat()
        }

        tickets.append(ticket)

        with open(
            TICKET_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                tickets,
                file,
                indent=4,
                ensure_ascii=False
            )

        return ticket