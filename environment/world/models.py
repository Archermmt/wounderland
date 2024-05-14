from django.db import models


# Create your models here.


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return "{}, email: {}".format(self.name, self.email)

    def all_llm_keys(self):
        return [
            {"key": k.key, "create": k.create_time.strftime("%Y%m%d %H:%M")}
            for k in self.llmkey_set.all()
        ]


class LLMKey(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now_add=True)
