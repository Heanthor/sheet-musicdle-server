from django import forms
from django.core.files.uploadedfile import UploadedFile

from sheet_api.models import Puzzle
from sheet_api.s3 import upload_sheet_music_file


class PuzzleForm(forms.ModelForm):
    sheet_music_image = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(PuzzleForm, self).__init__(*args, **kwargs)
        # since we are patching this form to upload the image, we don't want to enter a url ahead of time
        # but, we want to be able to view it in the change form
        self.fields["sheet_image_url"].required = False

    class Meta:
        model = Puzzle
        fields = "__all__"

    def save(self, commit=True):
        # get the image data from sheet_music_image, and call upload_to_s3
        image_form_data: UploadedFile = self.cleaned_data.get("sheet_music_image", None)

        if image_form_data:
            self.instance.sheet_image_url = upload_sheet_music_file(
                image_form_data.name, image_form_data.file
            )

        return super().save(commit)


class ScraperAdminForm(forms.Form):
    composer = forms.CharField()
    dry_run = forms.BooleanField(required=False, initial=True)
