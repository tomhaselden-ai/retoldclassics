class EPUBBuilder:
    def build(self,scenes):
        f=open('story.epub','w')
        [f.write(s+'\n') for s in scenes]
        f.close()
        return 'story.epub'
