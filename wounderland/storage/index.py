"""wounderland.storage.index"""

import os
from typing import List, Any
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.core.schema import TextNode
from llama_index import core as index_core
from wounderland import utils


class LLMEmbedding(index_core.embeddings.BaseEmbedding):
    def __init__(self, llm, *args, **kwargs):
        self._llm = llm
        super().__init__(*args, **kwargs)

    @classmethod
    def class_name(cls) -> str:
        return "llm_embedding"

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._llm.embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._llm.embedding(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._llm.embedding(t) for t in texts]


class QueryLLM(index_core.llms.CustomLLM):
    llm: Any = None
    context_window: int = 3900
    num_output: int = 256
    model_name: str = "custom"
    dummy_response: str = "Foo response"

    @property
    def metadata(self) -> index_core.llms.LLMMetadata:
        """Get LLM metadata."""
        return index_core.llms.LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model_name,
        )

    @llm_completion_callback()
    def complete(self, prompt, **kwargs) -> index_core.llms.CompletionResponse:
        response = self.llm.completion(prompt) if self.llm else self.dummy_response
        return index_core.llms.CompletionResponse(text=response)

    @llm_completion_callback()
    def stream_complete(
        self, prompt, **kwargs
    ) -> index_core.llms.CompletionResponseGen:
        response = ""
        for token in self.dummy_response:
            response += token
            yield index_core.llms.CompletionResponse(text=response, delta=token)


class LlamaIndex:
    def __init__(self, embedding, path=None, llm=None):
        self._config = {"max_nodes": 0}
        if embedding["type"] == "hugging_face":
            embed_model = HuggingFaceEmbedding(model_name=embedding["model"])
        else:
            raise NotImplementedError(
                "embedding type {} is not supported".format(embedding["type"])
            )
        service_context = index_core.ServiceContext.from_defaults(
            llm=QueryLLM(llm=llm), embed_model=embed_model, chunk_size=1024
        )
        if path and os.path.exists(path):
            self._index = index_core.load_index_from_storage(
                index_core.StorageContext.from_defaults(persist_dir=path),
                service_context=service_context,
                show_progress=True,
            )
            self._config = utils.load_dict(os.path.join(path, "index_config.json"))
        else:
            self._index = index_core.VectorStoreIndex(
                [], service_context=service_context, show_progress=True
            )
        self._path = path
        self._queryable = llm is not None

    def add_node(
        self,
        text,
        metadata=None,
        exclude_llm_keys=None,
        exclude_embedding_keys=None,
        id=None,
    ):
        metadata = metadata or {}
        exclude_llm_keys = exclude_llm_keys or list(metadata.keys())
        exclude_embedding_keys = exclude_embedding_keys or list(metadata.keys())
        id = id or "node_" + str(self._config["max_nodes"])
        self._config["max_nodes"] += 1
        node = TextNode(
            text=text,
            id_=id,
            metadata=metadata,
            excluded_llm_metadata_keys=exclude_llm_keys,
            excluded_embed_metadata_keys=exclude_embedding_keys,
        )
        self._index.insert_nodes([node])
        return node

    def find_node(self, node_id):
        return self._index.docstore.docs[node_id]

    def get_nodes(self, filter=None):
        def _check(node):
            if not filter:
                return True
            return filter(node)

        return [n for n in self._index.docstore.docs.values() if _check(n)]

    def remove_nodes(self, node_ids, delete_from_docstore=True):
        self._index.delete_nodes(node_ids, delete_from_docstore=delete_from_docstore)

    def retrieve(
        self,
        text,
        similarity_top_k=5,
        filters=None,
        node_ids=None,
        retriever_creator=None,
    ):
        retriever_creator = retriever_creator or VectorIndexRetriever
        return retriever_creator(
            self._index,
            similarity_top_k=similarity_top_k,
            filters=filters,
            node_ids=node_ids,
        ).retrieve(text)

    def query(
        self,
        text,
        similarity_top_k=5,
        text_qa_template=None,
        refine_template=None,
        filters=None,
        query_creator=None,
    ):
        kwargs = {
            "similarity_top_k": similarity_top_k,
            "text_qa_template": text_qa_template,
            "refine_template": refine_template,
            "filters": filters,
        }
        if query_creator:
            query_engine = query_creator(retriever=self._index.as_retriever(**kwargs))
        else:
            query_engine = self._index.as_query_engine(**kwargs)
        return query_engine.query(text)

    def save(self, path=None):
        path = path or self._path
        self._index.storage_context.persist(path)
        utils.save_dict(self._config, os.path.join(path, "index_config.json"))

    @property
    def nodes_num(self):
        return len(self._index.docstore.docs)

    @property
    def queryable(self):
        return self._queryable
