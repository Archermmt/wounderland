from django.db import models

# Create your models here.


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default="player")

    def __str__(self):
        return "{}, email: {}".format(self.name, self.email)

    @classmethod
    def safe_get(cls, name, password=None, email=None):
        user = cls.objects.filter(name=name)
        if user:
            if password and (password != user.first().password):
                return None, "password mismatch"
            return user.first(), ""
        if not password:
            return None, "missing password"
        if not email:
            return None, "missing email"
        user = cls(name=name, password=password, email=email or "")
        user.save()
        return user, ""

    def all_llm_keys(self):
        return [
            {"key": k.key, "create": k.create_time.strftime("%Y%m%d-%H:%M")}
            for k in self.llmkey_set.all()
        ]


class LLMKey(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    create_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}, create @ {}".format(
            self.key, self.create_time.strftime("%Y%m%d-%H:%M")
        )

    @classmethod
    def safe_get(cls, user_name, key, value=None):
        user, error = User.safe_get(user_name)
        if not user:
            return None, "Can not find user {}:{}".format(user_name, error)
        llmkey = cls.objects.filter(user=user, key=key)
        if llmkey:
            return llmkey.first(), ""
        if not value:
            return None, "missing value"
        llmkey = cls(user=user, key=key, value=value)
        llmkey.save()
        return llmkey, ""
