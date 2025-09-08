import { defineCollection, z } from 'astro:content';

const docs = defineCollection({
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    sidebar: z.boolean().optional()
  })
});

export const collections = { docs };
