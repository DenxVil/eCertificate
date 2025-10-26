# Contributing to Denx Certificate Generator

Thank you for your interest in contributing! We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### Suggesting Features

We love new ideas! Please open an issue with:
- A clear description of the feature
- Use cases and benefits
- Any implementation ideas you have

### Code Contributions

1. **Fork the repository**

2. **Create a branch**

3. 8486963487:AAGSxdnypIrT9rdLtUWywwwHj44HjM2j5co
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes**
   - Follow the existing code style
   - Add docstrings to functions
   - Update documentation if needed

5. **Test your changes**
   - Ensure all existing functionality still works
   - Test your new feature thoroughly
   - Check for Python syntax errors

6. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Wait for review

## Development Setup

```bash
# Clone your fork (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/eCertificate.git
cd eCertificate

# Or clone the original repository
# git clone https://github.com/DenxVil/eCertificate.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.sample .env
# Edit .env with your settings

# Run the application
python app.py
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comments for complex logic
- Write docstrings for functions and classes
- Keep functions focused and small

## Testing

Before submitting:
- Test the web interface
- Test the Telegram bot (if applicable)
- Verify database operations
- Check email functionality
- Test with different file formats (CSV, Excel)

## Documentation

If you add new features:
- Update README.md
- Add examples in QUICKSTART.md
- Update API documentation if applicable
- Add inline code comments

## Areas for Contribution

Current areas where we'd love help:
- [ ] Unit tests
- [ ] UI/UX improvements
- [ ] Additional certificate template formats
- [ ] Multiple language support
- [ ] Advanced template customization
- [ ] PDF certificate generation
- [ ] Database migration for PostgreSQL/MySQL
- [ ] Docker containerization
- [ ] API rate limiting
- [ ] User authentication system
- [ ] Certificate verification system

## Questions?

Feel free to open an issue with your questions!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for making Denx Certificate Generator better! 🎉
