# Applying the Zagu Form UI Update

This update changes the form UI only. It preserves the existing POST endpoint and all existing form field names. The patch updates `templates/form.html`; the supplied Zagu logo and product reference images must also be copied into `static/zagu/`.

## Option A: Apply the patch and copy the assets

Run these commands from the root folder of your repository:

```bash
# 1. Open your repository
cd /path/to/promo-system

# 2. Make sure you are on the branch that should receive the update
git switch main
git pull origin main

# 3. Create a separate working branch
git switch -c feat/zagu-form-ui

# 4. Apply the HTML/CSS/JavaScript patch
# Replace /path/to/form-ui.patch with the location of the attached patch file
git apply --check /path/to/form-ui.patch
git apply /path/to/form-ui.patch

# 5. Copy the provided Zagu assets into the Flask static folder
mkdir -p static/zagu
cp /path/to/zagu-ui-assets/zagu-logo.png static/zagu/zagu-logo.png
cp /path/to/zagu-ui-assets/mais-con-yelo.png static/zagu/mais-con-yelo.png
cp /path/to/zagu-ui-assets/creme-brulee.png static/zagu/creme-brulee.png
cp /path/to/zagu-ui-assets/red-velvet.png static/zagu/red-velvet.png

# 6. Verify the patch scope and whitespace
git status --short
git diff --check
git diff --name-only

# 7. Review the changes before committing
git diff -- templates/form.html

# 8. Commit and push the UI update
git add templates/form.html static/zagu/
git commit -m "Redesign Zagu promo form UI"
git push -u origin feat/zagu-form-ui
```

The expected changed paths are:

```text
templates/form.html
static/zagu/zagu-logo.png
static/zagu/mais-con-yelo.png
static/zagu/creme-brulee.png
static/zagu/red-velvet.png
```

## Option B: Use the complete asset package

If you prefer not to copy the image files individually, extract the attached `zagu-ui-update.zip` from the repository root. It contains the updated `templates/form.html` and the complete `static/zagu/` asset folder.

```bash
cd /path/to/promo-system
unzip -o /path/to/zagu-ui-update.zip

git status --short
git diff --check
git add templates/form.html static/zagu/
git commit -m "Redesign Zagu promo form UI"
git push -u origin feat/zagu-form-ui
```

Do **not** apply the patch and then overwrite `templates/form.html` from the complete package unless you intentionally want to repeat the same update. Choose either Option A or Option B.

## What the new interaction does

When the user submits the form, the submit button changes to `Saving promo data...`, shows a CSS loading spinner, becomes disabled to prevent duplicate submissions, and then proceeds with the existing POST request. When the existing Flask route returns `success=True`, the success message appears with a pop-in and checkmark pulse animation.

No backend route, Google Sheets logic, or field name was changed by this UI update.
