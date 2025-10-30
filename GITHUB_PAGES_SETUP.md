# GitHub Pages Deployment Guide

This document explains how to enable and configure GitHub Pages for the eCertificate project.

## What Was Deployed

The deployment includes:

1. **Static Landing Page** (`docs/index.html`) - A beautiful, standalone webpage showcasing the project
2. **GitHub Actions Workflow** (`.github/workflows/deploy-pages.yml`) - Automatically deploys to GitHub Pages
3. **404 Error Page** (`docs/404.html`) - Custom error page for missing pages
4. **Configuration** (`docs/_config.yml` and `docs/.nojekyll`) - GitHub Pages configuration

## Enabling GitHub Pages

After merging this PR, follow these steps to enable GitHub Pages:

### Step 1: Access Repository Settings

1. Go to your repository on GitHub: `https://github.com/DenxVil/eCertificate`
2. Click on the **Settings** tab (⚙️)

### Step 2: Configure GitHub Pages

1. In the left sidebar, click on **Pages** under "Code and automation"
2. Under **Source**, select:
   - Source: **GitHub Actions** (recommended)
   - This allows the workflow to deploy automatically
3. Click **Save**

### Step 3: Wait for Deployment

1. Go to the **Actions** tab in your repository
2. You should see the "Deploy to GitHub Pages" workflow running
3. Wait for it to complete (usually takes 1-2 minutes)
4. Once complete, your site will be live at: `https://denxvil.github.io/eCertificate/`

## Automatic Deployment

The GitHub Actions workflow (`.github/workflows/deploy-pages.yml`) will automatically deploy your site:

- **On every push to `main` branch** - Any changes to the `docs/` folder will trigger a new deployment
- **Manual trigger** - You can also manually run the workflow from the Actions tab

## Customizing the Landing Page

To update the landing page:

1. Edit files in the `docs/` directory:
   - `docs/index.html` - Main landing page
   - `docs/404.html` - Error page
   - `docs/_config.yml` - Site configuration

2. Commit and push changes to `main` branch
3. The workflow will automatically deploy the updates

## Troubleshooting

### Pages not deploying

If GitHub Pages isn't deploying:

1. Check the **Actions** tab for any failed workflows
2. Ensure GitHub Pages is enabled in Settings → Pages
3. Verify the workflow has the correct permissions (it's configured in the workflow file)

### 404 Errors

If you see 404 errors:

1. Ensure the `docs/.nojekyll` file exists (prevents Jekyll processing)
2. Check that file paths in HTML are relative (not absolute)
3. Verify the files exist in the `docs/` directory

### Changes not appearing

If your changes aren't showing up:

1. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Wait a few minutes for GitHub's CDN to update
3. Check the Actions tab to ensure deployment completed successfully

## Understanding the Deployment

### Why GitHub Pages?

GitHub Pages is perfect for hosting:
- Project documentation
- Landing pages
- Static marketing sites
- Demo pages

### Limitations

GitHub Pages **cannot** host the full Flask application because:
- It only serves static files (HTML, CSS, JS)
- No backend/server-side code execution
- No database connections
- No Python/Flask runtime

For the full application with certificate generation, use Azure, Heroku, or another platform that supports backend applications.

### What's Included

The landing page includes:
- ✅ Project overview and features
- ✅ Installation instructions
- ✅ Technology stack information
- ✅ Links to GitHub repository
- ✅ Quick start guide
- ✅ Responsive design that works on mobile and desktop

## Next Steps

After enabling GitHub Pages:

1. **Share the link** - `https://denxvil.github.io/eCertificate/`
2. **Update documentation** - Add the link to your README badges
3. **Add custom domain** (optional) - Configure a custom domain in Settings → Pages
4. **Monitor traffic** - Use GitHub Insights to see page views

## Support

If you encounter any issues:

1. Check the [GitHub Pages documentation](https://docs.github.com/pages)
2. Review the workflow logs in the Actions tab
3. Open an issue in the repository

---

**Note**: Remember that this is a static landing page. The full certificate generation application requires deployment to a backend hosting platform like Azure (which is already configured in this repository).
