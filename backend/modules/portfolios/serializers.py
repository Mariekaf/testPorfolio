from django.utils.text import slugify
from rest_framework import serializers
from .models import Portfolio

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ("id","name","slug","description","portfolio_type","status","visibility","created_at","updated_at")
        read_only_fields = ("id","status","visibility","created_at","updated_at")

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"name","slug","description","portfolio_type"}:
            raise serializers.ValidationError({"non_field_errors":["Champs non autorisés."]})
        return super().to_internal_value(data)

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Le nom doit contenir au moins 3 caractères.")
        return value.strip()

    def validate(self, attrs):
        if self.instance is None and "slug" not in attrs:
            attrs["slug"] = slugify(attrs.get("name",""), allow_unicode=False)[:110]
        if not attrs.get("slug") and self.instance is None:
            raise serializers.ValidationError({"slug":["Un slug valide est nécessaire."]})
        slug = attrs.get("slug")
        if slug and Portfolio.objects.filter(slug__iexact=slug).exclude(pk=getattr(self.instance,"pk",None)).exists():
            raise serializers.ValidationError({"slug":["Ce slug est déjà utilisé."]})
        return attrs
