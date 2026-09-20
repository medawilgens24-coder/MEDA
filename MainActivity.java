        });
    }

    private class NativeBridge {

        @JavascriptInterface
        public void print() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    try {
                        WebView w = getBridge().getWebView();
                        PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                        String job = "Meda";
                        PrintDocumentAdapter adapter = w.createPrintDocumentAdapter(job);
                        pm.print(job, adapter, new PrintAttributes.Builder().build());
                    } catch (Exception e) {
                        toast("Enpresyon pa disponib: " + e.getMessage());
                    }
                }
            });
        }

        @JavascriptInterface
        public void saveFile(String name, String base64, String mime) {
            try {
                byte[] data = Base64.decode(base64, Base64.DEFAULT);
                String safe = name.replaceAll("[\\\\/:*?\"<>|]", "_");
                String where;
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, safe);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    OutputStream os = getContentResolver().openOutputStream(uri);
                    os.write(data);
                    os.close();
                    where = "Downloads";
                } else {
                    File dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                    if (dir != null && !dir.exists()) dir.mkdirs();
                    File f = new File(dir, safe);
                    FileOutputStream fos = new FileOutputStream(f);
                    fos.write(data);
                    fos.close();
                    where = f.getParent();
                }
                toast("Fichye sove: " + safe + " (" + where + ")");
            } catch (Exception e) {
                toast("Erè pandan sovgad: " + e.getMessage());
