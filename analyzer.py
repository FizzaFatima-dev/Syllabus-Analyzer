def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (0.1, 0.7, 0.3), "IKS": (0.5, 0.2, 0.8), "STARTUP": (0.9, 0.2, 0.3)}
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '')
        # Skip if AI gave us a generic "No content" message
        if len(phrase) < 5 or "no specific" in phrase.lower(): 
            continue
            
        color = colors.get(item['theme'].upper(), (1, 1, 0))
        
        for page in doc:
            # We use 'quads=True' to handle text that might wrap to a new line
            # and 'small_caps=True' to handle different font styles
            search_instances = page.search_for(phrase, quads=True)

            if not search_instances:
                # SECOND ATTEMPT: Try searching word by word if the full phrase fails
                # This helps if there is a hidden newline character in the middle
                first_word = phrase.split()[0]
                search_instances = page.search_for(first_word, quads=True)

            for inst in search_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()