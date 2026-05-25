import React, { useState, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [view, setView] = useState('upload');
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [providers, setProviders] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState('All');

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setView('loading');
    const formData = new FormData();
    formData.append('file', selectedImage);

    try {
      const response = await axios.post('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setAnalysis(response.data);
      
      const providersRes = await axios.get('/api/providers');
      setProviders(providersRes.data);
      
      setView('results');
    } catch (error) {
      console.error("Analysis failed", error);
      alert("Something went wrong during analysis. Please try again.");
      setView('upload');
    }
  };

  const reset = () => {
    setView('upload');
    setSelectedImage(null);
    setPreviewUrl(null);
    setAnalysis(null);
  };

  const categories = ['All', ...new Set(providers.map(p => p.category))];
  const filteredProviders = categoryFilter === 'All' 
    ? providers 
    : providers.filter(p => p.category === categoryFilter);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm py-4 px-6 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary flex items-center gap-2" onClick={reset} style={{cursor: 'pointer'}}>
            <span className="text-accent">HouseFix</span> AI
          </h1>
          {view === 'results' && (
            <button onClick={reset} className="text-gray-500 hover:text-primary text-sm font-medium">
              Start Over
            </button>
          )}
        </div>
      </header>

      <main className="flex-grow p-6 max-w-4xl mx-auto w-full">
        {view === 'upload' && (
          <div className="space-y-8 animate-fade-in">
            <div className="text-center space-y-4">
              <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                Snap a photo of your home issue
              </h2>
              <p className="text-lg text-gray-600">
                Get an instant explanation and cost estimate from our AI.
              </p>
            </div>

            <div className="bg-white border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center transition-all hover:border-primary">
              {!previewUrl ? (
                <label className="cursor-pointer space-y-4 block">
                  <div className="bg-blue-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto">
                    <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                  <div className="text-gray-600">
                    <span className="font-semibold text-primary">Click to upload</span> or drag and drop
                    <p className="text-xs mt-1">PNG, JPG, WebP up to 10MB</p>
                  </div>
                  <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
                </label>
              ) : (
                <div className="space-y-6">
                  <img src={previewUrl} alt="Preview" className="max-h-64 mx-auto rounded-lg shadow-md" />
                  <div className="flex justify-center gap-4">
                    <label className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-600 hover:text-primary transition-colors">
                      Change Photo
                      <input type="file" className="hidden" accept="image/*" onChange={handleImageChange} />
                    </label>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={!selectedImage}
              className={`w-full py-4 rounded-xl text-lg font-bold transition-all shadow-lg ${
                selectedImage 
                  ? 'bg-primary text-white hover:bg-blue-700' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              Analyze Issue
            </button>
          </div>
        )}

        {view === 'loading' && (
          <div className="flex flex-col items-center justify-center py-20 space-y-6">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary"></div>
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900">Analyzing your photo...</h3>
              <p className="text-gray-500 mt-2">Our AI is identifying the issue and estimating costs.</p>
            </div>
          </div>
        )}

        {view === 'results' && analysis && (
          <div className="space-y-8 animate-fade-in">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="md:flex">
                <div className="md:w-1/3 bg-gray-100">
                  <img src={previewUrl} alt="Issue" className="w-full h-full object-cover max-h-64 md:max-h-none" />
                </div>
                <div className="p-6 md:w-2/3 space-y-4">
                  <div className="flex justify-between items-start">
                    <h2 className="text-2xl font-bold text-gray-900 capitalize">{analysis.issue_type}</h2>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                      analysis.confidence === 'high' ? 'bg-green-100 text-green-700' :
                      analysis.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {analysis.confidence} Confidence
                    </span>
                  </div>
                  <p className="text-gray-600 leading-relaxed">
                    {analysis.description}
                  </p>
                  <div className="pt-4 border-t border-gray-50">
                    <p className="text-sm text-gray-500 uppercase font-bold tracking-widest">Estimated Cost</p>
                    <p className="text-3xl font-black text-primary mt-1">{analysis.cost_range}</p>
                    <p className="text-xs text-gray-400 mt-1 italic">* This is a rough estimate. Actual costs may vary.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h3 className="text-xl font-bold text-gray-900">Nearby Service Providers</h3>
                <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
                  {categories.map(cat => (
                    <button
                      key={cat}
                      onClick={() => setCategoryFilter(cat)}
                      className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                        categoryFilter === cat 
                        ? 'bg-primary text-white shadow-md' 
                        : 'bg-white text-gray-600 border border-gray-200 hover:border-primary'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredProviders.map(provider => (
                  <div key={provider.id} className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 space-y-4 transition-transform hover:scale-[1.02]">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="px-2 py-0.5 bg-blue-50 text-primary text-[10px] font-bold uppercase rounded tracking-wider">
                          {provider.category}
                        </span>
                        <h4 className="text-lg font-bold text-gray-900 mt-1">{provider.name}</h4>
                        <div className="flex items-center gap-1 mt-1 text-yellow-400">
                          {[...Array(5)].map((_, i) => (
                            <svg key={i} className={`w-4 h-4 ${i < Math.floor(provider.rating) ? 'fill-current' : 'text-gray-200'}`} viewBox="0 0 20 20">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                          <span className="text-gray-400 text-xs ml-1">({provider.city})</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 pt-2">
                      <a
                        href={`https://wa.me/${provider.phone}?text=Hi ${provider.name}, I found you on HouseFix AI. I have a ${analysis.issue_type} and would like to chat about a repair.`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 py-2.5 px-4 bg-[#25D366] text-white rounded-lg text-xs font-bold hover:bg-[#128C7E] transition-colors"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L0 24l6.335-1.662c1.72.937 3.672 1.433 5.661 1.434h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
                        </svg>
                        WhatsApp
                      </a>
                      <button
                        onClick={() => alert("Quote requests coming soon!")}
                        className="py-2.5 px-4 bg-white border border-gray-200 text-gray-700 rounded-lg text-xs font-bold hover:bg-gray-50 transition-colors"
                      >
                        Request Quote
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-gray-100 py-8 px-6 text-center">
        <div className="max-w-4xl mx-auto space-y-2">
          <p className="text-gray-900 font-bold">HouseFix AI</p>
          <p className="text-gray-500 text-sm">Get quick estimates for your home repairs without the hassle.</p>
          <p className="text-gray-400 text-xs pt-4">2024 HouseFix AI</p>
        </div>
      </footer>
    </div>
  );
};

export default App;