# System Cleanup Checklist - Fresh Start

## ⚠️ WARNING
This will DELETE all Python and Node.js installations and packages. Do this only if you're ready to start fresh.

---

## PYTHON CLEANUP

### Step 1: Uninstall Python versions
Open **Settings → Apps → Installed Apps** and search for each:

- [ ] Uninstall **Python 3.10**
- [ ] Uninstall **Python 3.14**
- [ ] Keep **Python 3.13** (for this project)

After uninstalling, restart your PC.

### Step 2: Delete leftover folders
Open **File Explorer** and delete these folders (if they exist):

- [ ] `C:\Users\tomwt\AppData\Local\Programs\Python\Python310`
- [ ] `C:\Users\tomwt\AppData\Local\Programs\Python\Python314`
- [ ] `C:\Users\tomwt\AppData\Roaming\Python` (old global installs)

### Step 3: Clear pip cache
```bash
py -3.13 -m pip cache purge
```

---

## NODE.JS CLEANUP

### Step 1: Delete node_modules folders
These are in your project folders. Run this from your Projects directory:

```bash
# Find all node_modules folders
Get-ChildItem -Path "F:\Projects" -Recurse -Directory -Name "node_modules" -ErrorAction SilentlyContinue
```

Then delete them manually or use:
```bash
Get-ChildItem -Path "F:\Projects" -Recurse -Directory -Name "node_modules" -ErrorAction SilentlyContinue | ForEach-Object { Remove-Item -Path $_ -Recurse -Force }
```

### Step 2: Uninstall global npm packages
```bash
npm list -g --depth=0
```

Uninstall what you don't recognize:
```bash
npm uninstall -g <package-name>
```

---

## FRESH INSTALL - ONLY WHAT YOU NEED

### For the Subtitle Generator Project:
```bash
# Create venv
python -m venv venv
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

That's it. Everything is isolated in the venv.

### For OTHER projects later:
Create a NEW venv for each project. Never install globally again.

---

## OPTIONAL: Cache & Downloads Cleanup

If you want to be thorough:

### Step 1: Clear caches
```bash
# npm cache
npm cache clean --force

# pip cache  
py -3.13 -m pip cache purge
```

### Step 2: Delete cache folders (SAFE)
- [ ] `C:\Users\tomwt\.cache` → **8.25 GB** (old project caches)
- [ ] `C:\Users\tomwt\AppData\Local\Temp` → 0.73 GB (temp files)

### Step 3: Clean Downloads (CHECK FIRST!)
- [ ] Review `C:\Users\tomwt\Downloads` → **12.2 GB**
  - Delete old installers, files you don't recognize
  - Keep anything important

### Step 4: VS Code cleanup (OPTIONAL)
VS Code settings/extensions: 1.47 GB
- Only delete if you don't use VS Code
- Or just leave it (relatively small)

---

## DISK SPACE SAVED (Total)
- Python 3.10: ~3GB
- Python 3.14: ~6GB
- Roaming Python: ~3.6GB
- node_modules folders: ~2-5GB
- .cache folder: ~8GB
- Downloads: ~5-10GB (if cleaned)

**Total: ~30-35GB freed up** ✨

---

## After cleanup, your system will:
- Be ~15GB lighter
- Have zero global package pollution
- Be ready for venv-based development
- Start fresh whenever needed
