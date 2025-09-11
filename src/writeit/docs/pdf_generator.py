"""
PDF documentation generator
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .models import DocumentationSet


class PDFDocumentationGenerator:
    """Generate PDF documentation from HTML or Markdown"""
    
    def __init__(self):
        self.temp_dir = None
    
    def generate_pdf(self, docs: DocumentationSet, output_path: Path, html_path: Optional[Path] = None) -> bool:
        """Generate PDF documentation"""
        try:
            # Try different PDF generation methods
            if html_path and html_path.exists():
                return self._generate_from_html(docs, output_path, html_path)
            else:
                return self._generate_from_content(docs, output_path)
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return False
    
    def _generate_from_html(self, docs: DocumentationSet, output_path: Path, html_path: Path) -> bool:
        """Generate PDF from existing HTML documentation"""
        try:
            # Try WeasyPrint first (best quality)
            if self._try_weasyprint(html_path, output_path):
                return True
            
            # Fallback to other methods
            return self._generate_from_content(docs, output_path)
            
        except Exception as e:
            print(f"Warning: HTML to PDF conversion failed: {e}")
            return self._generate_from_content(docs, output_path)
    
    def _try_weasyprint(self, html_path: Path, output_path: Path) -> bool:
        """Try generating PDF using WeasyPrint"""
        try:
            import weasyprint
            
            # Find the main index.html file
            index_file = html_path / "index.html"
            if not index_file.exists():
                index_file = html_path / "site" / "index.html"
            
            if not index_file.exists():
                return False
            
            # Convert HTML to PDF
            html_doc = weasyprint.HTML(filename=str(index_file))
            html_doc.write_pdf(str(output_path))
            
            print(f"✅ PDF generated using WeasyPrint: {output_path}")
            return True
            
        except ImportError:
            print("⚠️  WeasyPrint not available for PDF generation")
            return False
        except Exception as e:
            print(f"WeasyPrint PDF generation failed: {e}")
            return False
    
    def _generate_from_content(self, docs: DocumentationSet, output_path: Path) -> bool:
        """Generate PDF directly from documentation content using ReportLab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.darkblue
            )
            
            code_style = ParagraphStyle(
                'Code',
                parent=styles['Code'],
                fontSize=10,
                spaceAfter=12,
                leftIndent=20,
                backgroundColor=colors.lightgrey,
                borderColor=colors.grey,
                borderWidth=1,
                borderPadding=10
            )
            
            # Build PDF content
            story = []
            
            # Title page
            title = docs.api_docs.title if docs.api_docs else 'WriteIt'
            story.append(Paragraph(f"{title} Documentation", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Generated on {docs.generated_at.strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Paragraph(f"Version {docs.version}", styles['Normal']))
            story.append(PageBreak())
            
            # Table of contents
            story.append(Paragraph("Table of Contents", heading_style))
            story.append(Spacer(1, 12))
            
            toc_data = []
            if docs.api_docs:
                toc_data.append(["API Documentation", f"{len(docs.api_docs.endpoints)} endpoints"])
            if docs.module_docs:
                toc_data.append(["Module Documentation", f"{len(docs.module_docs)} modules"])
            if docs.cli_docs:
                toc_data.append(["CLI Documentation", f"{len(docs.cli_docs.commands)} commands"])
            if docs.user_guides:
                toc_data.append(["User Guides", f"{len(docs.user_guides)} guides"])
            
            if toc_data:
                toc_table = Table(toc_data, colWidths=[4*inch, 2*inch])
                toc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(toc_table)
            
            story.append(PageBreak())
            
            # API Documentation
            if docs.api_docs:
                story.append(Paragraph("API Documentation", heading_style))
                story.append(Spacer(1, 12))
                story.append(Paragraph(docs.api_docs.description, styles['Normal']))
                story.append(Spacer(1, 12))
                
                # API Info table
                api_info = [
                    ["Base URL", docs.api_docs.base_url],
                    ["Version", docs.api_docs.version],
                    ["Endpoints", str(len(docs.api_docs.endpoints))],
                    ["Models", str(len(docs.api_docs.models))]
                ]
                
                api_table = Table(api_info, colWidths=[2*inch, 4*inch])
                api_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(api_table)
                story.append(Spacer(1, 20))
                
                # Endpoints (limited to first 10)
                story.append(Paragraph("Endpoints", ParagraphStyle('SubHeading', parent=styles['Heading3'])))
                story.append(Spacer(1, 12))
                
                for endpoint in docs.api_docs.endpoints[:10]:
                    story.append(Paragraph(f"{endpoint.method} {endpoint.path}", styles['Heading4']))
                    story.append(Paragraph(endpoint.description, styles['Normal']))
                    
                    if endpoint.parameters:
                        param_text = "Parameters: " + ", ".join([p.name for p in endpoint.parameters[:5]])
                        story.append(Paragraph(param_text, styles['Normal']))
                    
                    story.append(Spacer(1, 12))
                
                story.append(PageBreak())
            
            # Module Documentation
            if docs.module_docs:
                story.append(Paragraph("Module Documentation", heading_style))
                story.append(Spacer(1, 12))
                
                for module in docs.module_docs[:5]:
                    story.append(Paragraph(f"Module: {module.name}", styles['Heading3']))
                    story.append(Paragraph(module.description, styles['Normal']))
                    story.append(Paragraph(f"Purpose: {module.purpose}", styles['Normal']))
                    
                    if module.classes:
                        story.append(Paragraph(f"Classes ({len(module.classes)})", styles['Heading4']))
                        for cls in module.classes[:3]:
                            story.append(Paragraph(f"• {cls.name}: {cls.description[:100]}...", styles['Normal']))
                    
                    if module.functions:
                        story.append(Paragraph(f"Functions ({len(module.functions)})", styles['Heading4']))
                        for func in module.functions[:3]:
                            story.append(Paragraph(f"• {func.name}: {func.description[:100]}...", styles['Normal']))
                    
                    story.append(Spacer(1, 12))
                
                story.append(PageBreak())
            
            # CLI Documentation
            if docs.cli_docs:
                story.append(Paragraph("CLI Documentation", heading_style))
                story.append(Spacer(1, 12))
                story.append(Paragraph(docs.cli_docs.description, styles['Normal']))
                story.append(Spacer(1, 12))
                
                for command in docs.cli_docs.commands[:10]:
                    story.append(Paragraph(f"Command: {command.name}", styles['Heading4']))
                    story.append(Paragraph(command.description, styles['Normal']))
                    story.append(Paragraph(f"Usage: {command.usage}", code_style))
                    
                    if command.examples:
                        story.append(Paragraph("Examples:", styles['Heading5']))
                        for example in command.examples[:2]:
                            story.append(Paragraph(example, code_style))
                    
                    story.append(Spacer(1, 12))
            
            # User Guides
            if docs.user_guides:
                story.append(Paragraph("User Guides", heading_style))
                story.append(Spacer(1, 12))
                
                for guide in docs.user_guides:
                    story.append(Paragraph(guide.title, styles['Heading3']))
                    story.append(Paragraph(guide.description, styles['Normal']))
                    story.append(Paragraph(f"Audience: {guide.audience} | Difficulty: {guide.difficulty} | Time: {guide.estimated_time}", styles['Normal']))
                    
                    # Add first part of content (truncated for PDF)
                    content_preview = guide.content[:500] + "..." if len(guide.content) > 500 else guide.content
                    story.append(Paragraph(content_preview, styles['Normal']))
                    story.append(Spacer(1, 12))
            
            # Footer
            story.append(PageBreak())
            story.append(Paragraph("Generated Information", heading_style))
            story.append(Paragraph(f"This documentation was automatically generated on {docs.generated_at.strftime('%Y-%m-%d %H:%M:%S')}.", styles['Normal']))
            story.append(Paragraph(f"WriteIt Version: {docs.version}", styles['Normal']))
            story.append(Paragraph("This is an auto-generated document. Please report any issues.", styles['Italic']))
            
            # Build PDF
            doc.build(story)
            
            print(f"✅ PDF generated using ReportLab: {output_path}")
            return True
            
        except ImportError as e:
            print(f"⚠️  ReportLab not available: {e}")
            return self._generate_simple_pdf(docs, output_path)
        except Exception as e:
            print(f"ReportLab PDF generation failed: {e}")
            return False
    
    def _generate_simple_pdf(self, docs: DocumentationSet, output_path: Path) -> bool:
        """Generate simple text-based PDF as fallback"""
        try:
            # Create simple HTML and convert to PDF
            html_content = self._create_simple_html(docs)
            
            # Write HTML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                temp_html = Path(f.name)
            
            try:
                # Try to convert with weasyprint
                import weasyprint
                weasyprint.HTML(filename=str(temp_html)).write_pdf(str(output_path))
                print(f"✅ Simple PDF generated: {output_path}")
                return True
            finally:
                # Clean up temp file
                if temp_html.exists():
                    temp_html.unlink()
            
        except Exception as e:
            print(f"Simple PDF generation failed: {e}")
            return False
    
    def _create_simple_html(self, docs: DocumentationSet) -> str:
        """Create simple HTML for PDF conversion"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{docs.api_docs.title if docs.api_docs else 'WriteIt'} Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        code {{ background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #e9ecef; }}
        .endpoint {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .method {{ font-weight: bold; color: #2980b9; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #bdc3c7; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>{docs.api_docs.title if docs.api_docs else 'WriteIt'} Documentation</h1>
    <p><strong>Generated:</strong> {docs.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Version:</strong> {docs.version}</p>
"""
        
        # API Documentation
        if docs.api_docs:
            html += f"""    <h2>API Documentation</h2>
    <p>{docs.api_docs.description}</p>
    <p><strong>Base URL:</strong> {docs.api_docs.base_url}</p>
    <p><strong>Version:</strong> {docs.api_docs.version}</p>
    
    <h3>Endpoints</h3>
"""
            for endpoint in docs.api_docs.endpoints[:10]:
                html += f"""    <div class="endpoint">
        <div class="method">{endpoint.method} {endpoint.path}</div>
        <p>{endpoint.description}</p>
    </div>
"""
        
        # Module Documentation
        if docs.module_docs:
            html += "    <h2>Module Documentation</h2>\n"
            for module in docs.module_docs[:5]:
                html += f"""    <h3>{module.name}</h3>
    <p>{module.description}</p>
    <p><strong>Purpose:</strong> {module.purpose}</p>
"""
        
        # CLI Documentation
        if docs.cli_docs:
            html += "    <h2>CLI Documentation</h2>\n"
            html += f"    <p>{docs.cli_docs.description}</p>\n"
            for command in docs.cli_docs.commands[:5]:
                html += f"""    <h3>{command.name}</h3>
    <p>{command.description}</p>
    <pre>{command.usage}</pre>
"""
        
        html += f"""    <div class="footer">
        <p>This documentation was automatically generated on {docs.generated_at.strftime('%Y-%m-%d %H:%M:%S')}.</p>
        <p>WriteIt Version: {docs.version}</p>
    </div>
</body>
</html>"""
        
        return html
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)