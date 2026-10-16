from django.contrib.auth.base_user import BaseUserManager


def normalize_identity_email(value):
    return value.strip().lower()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        return self.get(email__iexact=normalize_identity_email(email))

    def create_user(self, email, password=None, **extra_fields):
        if not email or not email.strip():
            raise ValueError('An email address is required.')
        user = self.model(email=normalize_identity_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser flags must be true.')
        return self.create_user(email, password, **extra_fields)
