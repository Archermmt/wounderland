import json
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


class Agent(models.Model):
    name = models.CharField(max_length=100)
    record = models.DateTimeField(auto_now=True)
    status = models.TextField(max_length=500)
    schedule = models.TextField(max_length=5000)
    associate = models.TextField(max_length=500)
    chats = models.TextField(max_length=5000)
    currently = models.TextField(max_length=500)
    extra = models.TextField(max_length=5000)

    def to_dict(self):
        info = {
            "name": self.name,
            "status": json.loads(self.status),
            "schedule": json.loads(self.schedule),
            "associate": json.loads(self.associate),
            "chats": json.loads(self.chats),
            "currently": self.currently,
        }
        if self.extra:
            info.update(json.loads(self.extra))
        return info

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def get_last(cls, name, date):
        agent = cls.objects.filter(name=name, record__lt=date).order_by("-record")
        if not agent:
            return {}
        return agent.to_dict()

    @classmethod
    def from_dict(
        cls, name, record, status, schedule, associate, chats, currently, **extra
    ):
        agent = cls(
            name=name,
            record=record,
            status=json.dumps(status),
            schedule=json.dumps(schedule),
            associate=json.dumps(associate),
            chats=json.dumps(chats),
            currently=currently,
            extra=json.dumps(extra),
        )
        agent.save()
        return agent


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
