"""wounderland.model.llm_model"""

import os
import re
import json
import requests
from wounderland.utils.namespace import ModelType
from wounderland import utils


class ModelStyle:
    """Model Style"""

    OPEN_AI = "openai"
    QIANFAN = "qianfan"
    SPARK_AI = "sparkai"
    ZHIPU_AI = "zhipuai"


class LLMModel:
    def __init__(self, model, keys, config=None):
        self._model = model
        self._handle = self.setup(keys, config)
        self._meta_responses = []
        self._summary = {"total": [0, 0, 0]}

    def embedding(self, text, retry=1):
        response = None
        for _ in range(retry):
            try:
                response = self._embedding(text)
            except:
                continue
            if response:
                break
        return response

    def _embedding(self, text):
        raise NotImplementedError(
            "_embedding is not support for " + str(self.__class__)
        )

    def completion(
        self,
        prompt,
        retry=3,
        callback=None,
        failsafe=None,
        caller="llm_normal",
        **kwargs
    ):
        response, self._meta_responses = "", []
        self._summary.setdefault(caller, [0, 0, 0])
        for _ in range(retry):
            try:
                meta_response = self._completion(prompt, **kwargs)
                self._meta_responses.append(meta_response)
                self._summary["total"][0] += 1
                self._summary[caller][0] += 1
                if callback:
                    response = callback(meta_response)
                else:
                    response = meta_response
            except:
                response = ""
                continue
            if response:
                break
        pos = 1 if response else 2
        self._summary["total"][pos] += 1
        self._summary[caller][pos] += 1
        return response or failsafe

    def _completion(self, prompt, **kwargs):
        raise NotImplementedError(
            "_completion is not support for " + str(self.__class__)
        )

    def is_available(self):
        return self._summary["total"][2] <= 10

    def get_summary(self):
        des = {}
        for k, v in self._summary.items():
            des[k] = "S:{},F:{}/R:{}".format(v[1], v[2], v[0])
        return {"model": self._model, "summary": des}

    @property
    def meta_responses(self):
        return self._meta_responses

    @classmethod
    def model_type(cls):
        return ModelType.LLM


@utils.register_model
class OpenAILLMModel(LLMModel):
    def setup(self, keys, config):
        from openai import OpenAI

        self._embedding_model = config.get("embedding_model", "text-embedding-3-small")
        return OpenAI(api_key=keys["OPENAI_API_KEY"])

    def _embedding(self, text):
        response = self._handle.embeddings.create(
            input=text, model=self._embedding_model
        )
        return response.data[0].embedding

    def _completion(self, prompt, temperature=0.00001):
        messages = [{"role": "user", "content": prompt}]
        response = self._handle.chat.completions.create(
            model=self._model, messages=messages, temperature=temperature
        )
        if len(response.choices) > 0:
            return response.choices[0].message.content
        return ""

    @classmethod
    def support_model(cls, model):
        return model in ("gpt-3.5-turbo", "text-embedding-3-small")

    @classmethod
    def creatable(cls, keys, config):
        return "OPENAI_API_KEY" in keys

    @classmethod
    def model_style(cls):
        return ModelStyle.OPEN_AI


@utils.register_model
class ZhipuAILLMModel(LLMModel):
    def setup(self, keys, config):
        from zhipuai import ZhipuAI

        return ZhipuAI(api_key=keys["ZHIPUAI_API_KEY"])

    def _embedding(self, text):
        response = self._handle.embeddings.create(model="embedding-2", input=text)
        return response.data[0].embedding

    def _completion(self, prompt, temperature=0.00001):
        messages = [{"role": "user", "content": prompt}]
        response = self._handle.chat.completions.create(
            model=self._model, messages=messages, temperature=temperature
        )
        if len(response.choices) > 0:
            return response.choices[0].message.content
        return ""

    @classmethod
    def support_model(cls, model):
        return model in ("glm-4")

    @classmethod
    def creatable(cls, keys, config):
        return "ZHIPUAI_API_KEY" in keys

    @classmethod
    def model_style(cls):
        return ModelStyle.ZHIPU_AI


@utils.register_model
class QIANFANLLMModel(LLMModel):
    def setup(self, keys, config):
        handle = {k: keys[k] for k in ["QIANFAN_AK", "QIANFAN_SK"]}
        for k, v in handle.items():
            os.environ[k] = v
        return handle

    def _embedding(self, text):
        url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={0}&client_secret={1}".format(
            self._handle["QIANFAN_AK"], self._handle["QIANFAN_SK"]
        )
        payload = json.dumps("")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        url = (
            "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1?access_token="
            + str(response.json().get("access_token"))
        )
        input = []
        input.append(text)
        payload = json.dumps({"input": input})
        headers = {"Content-Type": "application/json"}
        # send request
        response = requests.request("POST", url, headers=headers, data=payload)
        response = json.loads(response.text)
        return response["data"][0]["embedding"]

    def _completion(self, prompt, temperature=0.00001):
        import qianfan

        messages = [{"role": "user", "content": prompt}]
        resp = qianfan.ChatCompletion().do(
            messages=messages, model=self._model, temperature=temperature
        )
        return resp["result"]

    @classmethod
    def support_model(cls, model):
        return model in ("ERNIE-Bot", "Yi-34B-Chat")

    @classmethod
    def creatable(cls, keys, config):
        return "QIANFAN_AK" in keys and "QIANFAN_SK" in keys

    @classmethod
    def model_style(cls):
        return ModelStyle.QIANFAN


@utils.register_model
class SparkAILLMModel(LLMModel):
    def setup(self, keys, config):
        spark_url_tpl = "wss://spark-api.xf-yun.com/{}/chat"
        handle = {"params": {}, "keys": {}}
        if self._model == "spark_v1.5":
            handle["params"] = {
                "domain": "general",  # 用于配置大模型版本
                "spark_url": spark_url_tpl.format("v1.1"),  # 云端环境的服务地址
            }
        elif self._model == "spark_v2.0":
            handle["params"] = {
                "domain": "generalv2",  # 用于配置大模型版本
                "spark_url": spark_url_tpl.format("v2.1"),  # 云端环境的服务地址
            }
        elif self._model == "spark_v3.0":
            handle["params"] = {
                "domain": "generalv3",  # 用于配置大模型版本
                "spark_url": spark_url_tpl.format("v3.1"),  # 云端环境的服务地址
            }
        elif self._model == "spark_v3.5":
            handle["params"] = {
                "domain": "generalv3.5",  # 用于配置大模型版本
                "spark_url": spark_url_tpl.format("v3.5"),  # 云端环境的服务地址
            }
        needed_keys = ["SPARK_APPID", "SPARK_API_SECRET", "SPARK_API_KEY"]
        handle["keys"] = {k: keys[k] for k in needed_keys}
        return handle

    def _completion(self, prompt, temperature=0.00001, streaming=False):
        from sparkai.llm.llm import ChatSparkLLM
        from sparkai.core.messages import ChatMessage

        spark_llm = ChatSparkLLM(
            spark_api_url=self._handle["params"]["spark_url"],
            spark_app_id=self._handle["keys"]["SPARK_APPID"],
            spark_api_key=self._handle["keys"]["SPARK_API_KEY"],
            spark_api_secret=self._handle["keys"]["SPARK_API_SECRET"],
            spark_llm_domain=self._handle["params"]["domain"],
            temperature=temperature,
            streaming=streaming,
        )
        messages = [ChatMessage(role="user", content=prompt)]
        resp = spark_llm.generate([messages])
        return resp

    @classmethod
    def support_model(cls, model):
        return model in ("spark_v1.5", "spark_v2.1", "spark_v3.1", "spark_v3.5")

    @classmethod
    def creatable(cls, keys, config):
        needed_keys = ["SPARK_APPID", "SPARK_API_SECRET", "SPARK_API_KEY"]
        return all(k in keys for k in needed_keys)

    @classmethod
    def model_style(cls):
        return ModelStyle.SPARK_AI


def create_llm_model(model, keys, config=None):
    """Create llm model"""

    for _, model_cls in utils.get_registered_model(ModelType.LLM).items():
        if model_cls.support_model(model) and model_cls.creatable(keys, config):
            return model_cls(model, keys, config=config)
    return None


def parse_llm_output(response, patterns, mode="match_last", ignore_empty=False):
    if isinstance(patterns, str):
        patterns = [patterns]
    rets = []
    for line in response.split("\n"):
        for pattern in patterns:
            if pattern:
                matchs = re.findall(pattern, line)
            else:
                matchs = [line]
            if len(matchs) == 1:
                rets.append(matchs[0])
                break
    if not ignore_empty:
        assert rets, "Failed to match llm output"
    if mode == "match_first":
        return rets[0]
    if mode == "match_last":
        return rets[-1]
    if mode == "match_all":
        return rets
    return None
