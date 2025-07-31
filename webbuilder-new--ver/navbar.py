new_navbar = '''
            <nav class="navbar navbar-expand-lg">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">Your Brand</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
            '''
            
            for page in pages:
                page_filename = 'index.html' if page.lower() == 'home' else f"{page.lower().replace(' ', '-')}.html"
                new_navbar += f'''
                            <li class="nav-item">
                                <a class="nav-link" href="{page_filename}">{page}</a>
                            </li>
                '''
            
            new_navbar += '''
                        </ul>
                    </div>
                </div>
            </nav>
            '''